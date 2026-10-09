"""Interchangeable image suggestions; neither provider decides sorting or pickup."""
from dataclasses import dataclass, field
from typing import Protocol
from .clarifications import question_for


@dataclass(frozen=True)
class Suggestion:
    item_id: str
    usage: dict = field(default_factory=dict)
    # Development evaluation may inspect these; application logs never include them.
    labels: tuple = ()
    clarification: str | None = None


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
MAPPING_VERSION = '2026-10-09.3'


def confident_labels(labels):
    return {label['Name'].strip().lower() for label in labels
            if isinstance(label.get('Name'), str)
            and isinstance(label.get('Confidence'), (int, float))
            and MIN_CONFIDENCE <= label['Confidence'] <= 100}


def map_labels(labels, catalogue):
    allowed = {item['id'] for item in catalogue['items']}
    candidates = set()
    confident_names = confident_labels(labels)
    for name in confident_names:
        item_id = LABEL_TO_CATALOGUE.get(name)
        if item_id in allowed:
            candidates.add(item_id)
    if {'jar', 'plastic'} <= confident_names and 'rigid-plastic' in allowed:
        candidates.add('rigid-plastic')
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
        # Do not narrow conflicting recognised objects into a misleading question.
        known = {LABEL_TO_CATALOGUE[n] for n in names if n in LABEL_TO_CATALOGUE}
        question = question_for(names) if item_id == 'unknown' and len(known) <= 1 else None
        return Suggestion(item_id, {
            'image_requests': 1,
            'label_model_version': response.get('LabelModelVersion'),
            'mapping_version': MAPPING_VERSION,
        }, labels=tuple({'name':label.get('Name'), 'confidence':label.get('Confidence')}
                        for label in labels), clarification=question)


def make_recognizer(provider, session):
    from botocore.config import Config
    config = Config(connect_timeout=2, read_timeout=18, retries={'total_max_attempts': 1})
    if provider == 'rekognition':
        return RekognitionRecognizer(session.client('rekognition', region_name='ap-south-1', config=config))
    if provider == 'bedrock':
        return BedrockRecognizer(session.client('bedrock-runtime', region_name='ap-south-1', config=config))
    raise ValueError('Unsupported recognition provider')
