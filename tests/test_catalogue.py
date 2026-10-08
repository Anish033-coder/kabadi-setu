import json
from pathlib import Path

CATALOGUE = json.loads((Path(__file__).parents[1] / 'data/catalogue.json').read_text())
ITEMS = {item['id']: item for item in CATALOGUE['items']}
STREAMS = {'wet', 'dry', 'sanitary', 'special_care', 'e_waste', 'unresolved'}

def test_every_item_uses_a_known_stream():
    for item in ITEMS.values():
        assert item['stream'] in STREAMS, item['id']

def test_streams_follow_the_cited_rules():
    assert ITEMS['battery']['stream'] == 'special_care'
    assert ITEMS['bulb']['stream'] == 'special_care'
    assert ITEMS['medicine']['stream'] == 'special_care'
    assert ITEMS['broken-glass']['stream'] == 'dry'
    assert ITEMS['electronics']['stream'] == 'e_waste'

def test_items_outside_ordinary_scrap_never_enter_the_basket():
    for item in ITEMS.values():
        if item['stream'] in ('wet', 'sanitary', 'special_care', 'e_waste', 'unresolved'):
            assert not item['candidate'], item['id']
