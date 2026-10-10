"""Interchangeable image suggestions; neither provider decides sorting or pickup."""
from dataclasses import dataclass, field
from typing import Protocol
from .clarifications import shortlist


@dataclass(frozen=True)
class Suggestion:
    item_id: str
    usage: dict = field(default_factory=dict)
    # Development evaluation may inspect these; application logs never include them.
    labels: tuple = ()
    clarification: str | None = None
    options: tuple = ()


class Recognizer(Protocol):
    provider: str
    model_id: str

    def recognize(self, raw: bytes, catalogue: dict) -> Suggestion: ...


class BedrockRecognizer:
    provider = 'bedrock'
    model_id = 'apac.amazon.nova-lite-v1:0'

    def __init__(self, client):
        self.client = client

    def recognize(self, raw, catalogue):
        # Keep these functions available to the existing opt-in probe.
        from .recognition import infer, parse_suggestion
        response = infer(self.client, raw, catalogue, self.model_id)
        usage = response.get('usage', {})
        return Suggestion(parse_suggestion(response, catalogue), {
            'input_tokens': usage.get('inputTokens'),
            'output_tokens': usage.get('outputTokens'),
        })


# Deliberately omit broad labels such as Paper, Bottle, Box and Metal: they do
# not establish the catalogue's item/material. Extend only after dev-set review.
LABEL_TO_CATALOGUE = {
    'newspaper': 'newspaper',
    'cardboard': 'cardboard',
    'cardboard box': 'cardboard',
    'notebook': 'notebooks',
    'plastic bottle': 'pet-bottle',
    'glass bottle': 'glass-bottle',
    'battery': 'battery',
    'mobile phone': 'electronics',
    'cell phone': 'electronics',
    'laptop': 'electronics',
    'computer': 'electronics',
    'light bulb': 'bulb',
    'fluorescent lamp': 'bulb',
}
MIN_CONFIDENCE = 90
MAPPING_VERSION = '2026-10-10.4'


def confident_labels(labels):
    return {label['Name'].strip().lower() for label in labels
            if isinstance(label.get('Name'), str)
            and isinstance(label.get('Confidence'), (int, float))
            and MIN_CONFIDENCE <= label['Confidence'] <= 100}


def specific_items(names, catalogue):
    allowed = {item['id'] for item in catalogue['items']}
    candidates = {LABEL_TO_CATALOGUE.get(name) for name in names} & allowed
    if {'jar', 'plastic'} <= names and 'rigid-plastic' in allowed:
        candidates.add('rigid-plastic')
    return candidates


def map_labels(labels, catalogue):
    candidates = specific_items(confident_labels(labels), catalogue)
    # Never choose the highest label when two different supported items appear.
    return next(iter(candidates)) if len(candidates) == 1 else 'unknown'


class RekognitionRecognizer:
    provider = 'rekognition'
    model_id = 'DetectLabels:GENERAL_LABELS'

    def __init__(self, client):
        self.client = client

    def recognize(self, raw, catalogue):
        response = self.client.detect_labels(
            Image={'Bytes': raw}, Features=['GENERAL_LABELS'],
            MaxLabels=50, MinConfidence=MIN_CONFIDENCE,
        )
        labels = response.get('Labels', [])
        item_id = map_labels(labels, catalogue)
        names = confident_labels(labels)
        # Broad or conflicting labels become a short list for the person, never a guess.
        kind, options = (shortlist(names, catalogue, sorted(specific_items(names, catalogue)))
                         if item_id == 'unknown' else (None, ()))
        return Suggestion(item_id, {
            'image_requests': 1,
            'label_model_version': response.get('LabelModelVersion'),
            'mapping_version': MAPPING_VERSION,
        }, labels=tuple({'name':label.get('Name'), 'confidence':label.get('Confidence')}
                        for label in labels), clarification=kind, options=options)


def make_recognizer(provider, session):
    from botocore.config import Config
    config = Config(connect_timeout=2, read_timeout=18, retries={'total_max_attempts': 1})
    if provider == 'rekognition':
        return RekognitionRecognizer(session.client('rekognition', region_name='ap-south-1', config=config))
    if provider == 'bedrock':
        return BedrockRecognizer(session.client('bedrock-runtime', region_name='ap-south-1', config=config))
    raise ValueError('Unsupported recognition provider')
