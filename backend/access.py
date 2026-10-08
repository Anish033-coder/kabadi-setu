from pathlib import Path
import cedarpy
from .domain import Problem

POLICIES = (Path(__file__).resolve().parent.parent / 'policies/access.cedar').read_text()

def check_access(doc, source, action, owner=None):
    kind = 'Household' if source == 'household' else 'PickupLink'
    identifier = owner if source == 'household' else doc['id']
    principal = {'type': kind, 'id': identifier}
    resource = {'type': 'Request', 'id': doc['id']}
    entities = [
        {'uid': principal, 'attrs': {'requestId': doc['id']} if kind == 'PickupLink' else {}, 'parents': []},
        {'uid': resource, 'attrs': {'owner': {'__entity': {'type': 'Household', 'id': doc['owner']}}, 'requestId': doc['id']}, 'parents': []}
    ]
    # Link validity (hash match, expiry, cancellation) is checked before this call in Service.authorised.
    result = cedarpy.is_authorized({'principal': principal, 'action': {'type': 'Action', 'id': action}, 'resource': resource,
                                   'context': {}}, POLICIES, entities)
    if not result.allowed:
        raise Problem(403, 'This action is not permitted.')
