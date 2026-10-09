"""Interchangeable image suggestions; neither provider decides sorting or pickup."""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Suggestion:
    item_id: str
    usage: dict = field(default_factory=dict)


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
MAPPING_VERSION = '2026-10-09.1'


def map_labels(labels, catalogue):
    allowed = {item['id'] for item in catalogue['items']}
    candidates = set()
    for label in labels:
        name, confidence = label.get('Name'), label.get('Confidence')
        if not isinstance(name, str) or not isinstance(confidence, (int, float)):
            continue
        if not MIN_CONFIDENCE <= confidence <= 100:
            continue
        item_id = LABEL_TO_CATALOGUE.get(name.strip().lower())
        if item_id in allowed:
            candidates.add(item_id)
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
        return Suggestion(map_labels(response.get('Labels', []), catalogue), {
            'image_requests': 1,
            'label_model_version': response.get('LabelModelVersion'),
            'mapping_version': MAPPING_VERSION,
        })


def make_recognizer(provider, session):
    from botocore.config import Config
    config = Config(connect_timeout=2, read_timeout=18, retries={'total_max_attempts': 1})
    if provider == 'rekognition':
        return RekognitionRecognizer(session.client('rekognition', region_name='ap-south-1', config=config))
    if provider == 'bedrock':
        return BedrockRecognizer(session.client('bedrock-runtime', region_name='ap-south-1', config=config))
    raise ValueError('Unsupported recognition provider')
