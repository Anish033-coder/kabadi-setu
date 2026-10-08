"""Application rules shared by the local adapter and Lambda."""
import hashlib
import hmac
import json
import time
import uuid


class Problem(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class Conflict(Problem):
    def __init__(self):
        super().__init__(409, "This request changed. Refresh it before trying again.")


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def action_key(value):
    if not isinstance(value, str) or not 16 <= len(value) <= 64 or not all(c.isalnum() or c in '-_' for c in value):
        raise Problem(400, "A valid action ID is required.")
    return value


REPLY_WINDOW = 48 * 3600
PICKUP_WINDOW = 7 * 24 * 3600
# DynamoDB TTL only cleans up old records; expiry decisions are always made in code.
RECORD_LIFETIME = 90 * 24 * 3600


class Service:
    def __init__(self, repository, catalogue, secret, clock=time.time):
        self.repo, self.catalogue, self.secret, self.clock = repository, catalogue, secret, clock
        self.items = {item['id']: item for item in catalogue['items']}

    def route(self, item_id, answers):
        item = self.items.get(item_id)
        if not item:
            raise Problem(400, 'Choose an item from the catalogue.')
        if not isinstance(answers, dict):
            raise Problem(400, 'Answers must be an object.')
        if item.get('check_clean') and answers.get('clean') not in ('yes', 'no', 'unsure'):
            return {'stream': 'unresolved', 'eligible': False, 'reason': 'Confirm whether it is empty, clean and dry.', 'reason_hi': 'बताएँ: क्या यह खाली, साफ़ और सूखा है?'}
        eligible = item.get('candidate', False) and answers.get('clean') == 'yes'
        return {'stream': item['stream'], 'eligible': eligible,
                'reason': item['guidance'] if not item.get('check_clean') or eligible else 'Keep it out of the basket until its condition is checked. Do not mix hazardous containers with ordinary scrap.',
                'reason_hi': item['guidance_hi'] if not item.get('check_clean') or eligible else 'स्थिति जाँचने तक इसे टोकरी से बाहर रखें। खतरनाक सामग्री के डिब्बे सामान्य कबाड़ में न मिलाएँ।',
                'acceptance': 'unknown', 'rule_version': self.catalogue['version']}

    def basket(self, rows):
        if not isinstance(rows, list) or len(rows) > 20:
            raise Problem(400, 'Use at most 20 basket entries.')
        result, seen = [], set()
        for row in rows:
            if not isinstance(row, dict):
                raise Problem(400, 'Invalid basket entry.')
            item = self.items.get(row.get('id'))
            quantity = row.get('quantity')
            if not item or item['id'] in seen or type(quantity) is not int or not 1 <= quantity <= 99:
                raise Problem(400, 'Choose distinct items with counts from 1 to 99.')
            answers = row.get('answers', {})
            if not self.route(item['id'], answers)['eligible']:
                raise Problem(400, 'An unconfirmed or unsupported item cannot enter this basket.')
            seen.add(item['id'])
            result.append({'id': item['id'], 'en': item['en'], 'hi': item['hi'], 'quantity': quantity, 'answers': answers})
        return result

    def save_basket(self, owner, rows):
        items = self.basket(rows)
        self.repo.put('BASKET#' + owner, {'items': items})
        return {'items': items}

    def token(self, request_id):
        return hmac.new(self.secret.encode(), request_id.encode(), hashlib.sha256).hexdigest()

    def replay_create(self, owner, receipt, fingerprint):
        if receipt['fingerprint'] != fingerprint:
            raise Problem(409, 'This action ID was already used with different items.')
        doc = self.get(receipt['id'], owner=owner)
        return {**doc, 'token': self.token(doc['id'])}

    def create(self, owner, body, key):
        key = action_key(key)
        rows = self.basket(body.get('items'))
        if not rows:
            raise Problem(400, 'Add at least one item first.')
        language = 'hi' if body.get('language') == 'hi' else 'en'
        fingerprint = digest(json.dumps({'items': rows, 'language': language}, sort_keys=True))
        receipt_key = 'CREATE#' + owner + '#' + key
        old = self.repo.get(receipt_key)
        if old:
            return self.replay_create(owner, old, fingerprint)
        now = int(self.clock())
        request_id = str(uuid.uuid4())
        doc = {'id': request_id, 'owner': owner, 'items': rows, 'language': language,
               'status': 'awaiting_response', 'version': 1, 'created_at': now, 'expires_at': now + REPLY_WINDOW,
               'rule_version': self.catalogue['version'], 'token_hash': digest(self.token(request_id)),
               'events': [{'action': 'created', 'source': 'household', 'at': now}], 'ttl': now + RECORD_LIFETIME}
        try:
            self.repo.create_request(doc, receipt_key, {'id': request_id, 'fingerprint': fingerprint, 'ttl': now + RECORD_LIFETIME})
        except Conflict:
            # A double tap can reach us twice at once; if the other copy committed, return its result.
            old = self.repo.get(receipt_key)
            if not old:
                raise
            return self.replay_create(owner, old, fingerprint)
        return {**self.public(doc), 'token': self.token(request_id)}

    def authorised(self, request_id, owner=None, token=None):
        doc = self.repo.get('REQUEST#' + request_id)
        if not doc:
            raise Problem(404, 'Request not found.')
        if owner and hmac.compare_digest(doc['owner'], owner):
            return doc, 'household'
        if isinstance(token, str) and len(token) == 64 and hmac.compare_digest(doc['token_hash'], digest(token)):
            if self.deadline(doc) <= self.clock() or doc['status'] == 'cancelled':
                raise Problem(410, 'This link has expired or was cancelled.')
            return doc, 'pickup_link'
        raise Problem(404, 'Request not found.')

    def deadline(self, doc):
        # The reply window covers an unanswered request; acceptance opens a separate pickup window.
        return doc.get('pickup_until') or doc['expires_at']

    def public(self, doc):
        public = {k: v for k, v in doc.items() if k not in ('owner', 'token_hash', 'ttl')}
        if public['status'] in ('awaiting_response', 'accepted') and self.deadline(public) <= self.clock():
            public['status'] = 'expired'
        return public

    def get(self, request_id, owner=None, token=None):
        from .access import check_access
        doc, source = self.authorised(request_id, owner, token)
        check_access(doc, source, 'view', owner)
        return self.public(doc)

    def replay_action(self, receipt, fingerprint):
        if receipt['fingerprint'] != fingerprint:
            raise Problem(409, 'This action ID was used for a different operation.')
        return receipt['result']

    def act(self, request_id, body, key, owner=None, token=None):
        from .access import check_access
        doc, source = self.authorised(request_id, owner, token)
        check_access(doc, source, body.get('action', ''), owner)
        receipt_key = f'ACTION#{request_id}#{source}#{action_key(key)}'
        fingerprint = digest(json.dumps({'action': body.get('action'), 'version': body.get('version')}, sort_keys=True))
        old = self.repo.get(receipt_key)
        if old:
            return self.replay_action(old, fingerprint)
        if type(body.get('version')) is not int or body['version'] != doc['version']:
            raise Conflict()
        state = self.public(doc)['status']
        transitions = ({'awaiting_response': {'accept': 'accepted', 'reject': 'rejected'}, 'accepted': {'collect': 'collection_reported'}}
                       if source == 'pickup_link' else
                       {'awaiting_response': {'cancel': 'cancelled'}, 'accepted': {'cancel': 'cancelled', 'collect': 'collection_reported'}})
        next_state = transitions.get(state, {}).get(body.get('action'))
        if not next_state:
            raise Problem(409, 'That action is not available for this request.')
        now = int(self.clock())
        updated = {**doc, 'status': next_state, 'version': doc['version'] + 1,
                   'events': [*doc['events'], {'action': body['action'], 'source': source, 'at': now}]}
        if next_state == 'accepted':
            updated['pickup_until'] = now + PICKUP_WINDOW
        result = self.public(updated)
        try:
            self.repo.transition(updated, doc['version'], receipt_key, {'fingerprint': fingerprint, 'result': result, 'ttl': now + RECORD_LIFETIME})
        except Conflict:
            old = self.repo.get(receipt_key)
            if not old:
                raise
            return self.replay_action(old, fingerprint)
        return result
