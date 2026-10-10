import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from backend.recognizers import RekognitionRecognizer, map_labels, make_recognizer

CATALOGUE = json.loads((Path(__file__).parents[1] / 'data/catalogue.json').read_text())


def labels(*names, confidence=99):
    return [{'Name': name, 'Confidence': confidence} for name in names]


@pytest.mark.parametrize('names,expected', [
    (['Newspaper', 'Paper'], 'newspaper'),
    (['Cardboard', 'Cardboard Box'], 'cardboard'),
    (['Laptop', 'Computer'], 'electronics'),
    (['Beer Bottle', 'Bottle', 'Beer'], 'unknown'),
    (['Jar', 'Plastic'], 'rigid-plastic'),
    (['Jar'], 'unknown'),
    (['Can', 'Aluminium', 'Tin'], 'unknown'),
    (['Beer Bottle', 'Plastic Bottle'], 'pet-bottle'),
    (['Bottle', 'Plastic'], 'unknown'),
    (['Metal', 'Can'], 'unknown'),
    (['Newspaper', 'Battery'], 'unknown'),
    (['Unknown Label'], 'unknown'),
    ([], 'unknown'),
])
def test_conservative_label_mapping(names, expected):
    assert map_labels(labels(*names), CATALOGUE) == expected


def test_low_confidence_and_removed_catalogue_items_are_unknown():
    assert map_labels(labels('Newspaper', confidence=89.9), CATALOGUE) == 'unknown'
    assert map_labels(labels('Newspaper'), {'items': []}) == 'unknown'
    assert map_labels([{'Name': 'Newspaper', 'Confidence': float('nan')}], CATALOGUE) == 'unknown'


def test_rekognition_uses_exact_bytes_and_only_general_labels():
    client = Mock()
    client.detect_labels.return_value = {'Labels': labels('Newspaper'), 'LabelModelVersion': '3.0'}
    result = RekognitionRecognizer(client).recognize(b'validated bytes', CATALOGUE)
    client.detect_labels.assert_called_once_with(
        Image={'Bytes': b'validated bytes'}, Features=['GENERAL_LABELS'], MaxLabels=50, MinConfidence=90)
    assert result.item_id == 'newspaper'
    assert result.usage['image_requests'] == 1
    assert result.usage['label_model_version'] == '3.0'
    assert 'input_tokens' not in result.usage
    assert result.labels == ({'name':'Newspaper', 'confidence':99},)
    assert 'labels' not in result.usage


def test_invalid_provider_fails_without_creating_client():
    session = Mock()
    with pytest.raises(ValueError): make_recognizer('typo', session)
    session.client.assert_not_called()


@pytest.mark.parametrize('names,kind,options', [
    (['Beer Bottle'], 'bottle', ('pet-bottle', 'glass-bottle')),
    (['Bottle', 'Plastic'], 'bottle', ('pet-bottle', 'glass-bottle', 'rigid-plastic')),
    (['Book', 'Publication', 'Text'], 'paper', ('newspaper', 'notebooks', 'office-paper', 'cardboard')),
    (['Advertisement', 'Poster'], 'paper', ('newspaper', 'notebooks', 'office-paper', 'cardboard')),
    (['Box'], 'box', ('cardboard',)),
    (['Can', 'Tin', 'Aluminium'], 'can', ('aluminium-can', 'steel-utensil')),
    (['Aluminium', 'Bottle', 'Shaker'], 'bottle', ('pet-bottle', 'glass-bottle', 'steel-utensil', 'aluminium-can')),
    (['Remote Control'], 'electronics', ('electronics',)),
    # Two specific items in one photo: offer both first, never pick one.
    (['Bottle', 'Newspaper', 'Battery'], 'items', ('battery', 'newspaper', 'pet-bottle', 'glass-bottle')),
    (['Ice'], None, ()),
    (['Grenade', 'Weapon'], None, ()),
])
def test_broad_labels_offer_a_short_list_instead_of_guessing(names, kind, options):
    client=Mock()
    client.detect_labels.return_value={'Labels':labels(*names)}
    result=RekognitionRecognizer(client).recognize(b'image', CATALOGUE)
    assert result.item_id == 'unknown'
    assert (result.clarification, result.options) == (kind, options)
    assert client.detect_labels.call_count == 1


def test_a_named_item_gets_no_short_list():
    client=Mock()
    client.detect_labels.return_value={'Labels':labels('Newspaper', 'Paper', 'Text')}
    result=RekognitionRecognizer(client).recognize(b'image', CATALOGUE)
    assert (result.item_id, result.options) == ('newspaper', ())


def test_short_list_is_catalogue_scoped_and_capped():
    from backend.clarifications import options_for, shortlist, MAX_CHOICES
    assert shortlist({'bottle'}, {'items':[{'id':'glass-bottle'}]}) == ('bottle', ('glass-bottle',))
    assert shortlist({'bottle'}, {'items':[]}) == (None, ())
    assert options_for(['untrusted', 'pet-bottle'], CATALOGUE) == ['pet-bottle']
    many = {'paper', 'bottle', 'jar', 'aluminium', 'remote control'}
    assert len(shortlist(many, CATALOGUE)[1]) == MAX_CHOICES
