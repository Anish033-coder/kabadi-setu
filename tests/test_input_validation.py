import json
from pathlib import Path
import pytest
from backend.domain import Service, Problem
from backend.repository import MemoryRepository

@pytest.fixture
def service():
    catalogue = json.loads((Path(__file__).parents[1] / 'data/catalogue.json').read_text())
    return Service(MemoryRepository(), catalogue, 'test-secret')

@pytest.mark.parametrize('item_id', [[], {}, ['newspaper'], {'id': 'newspaper'}, None, True])
def test_invalid_item_id_is_a_client_error(service, item_id):
    with pytest.raises(Problem) as error:
        service.route(item_id, {'clean': 'yes'})
    assert error.value.status == 400

@pytest.mark.parametrize('item_id', [[], {}, ['newspaper']])
def test_invalid_basket_id_is_a_client_error(service, item_id):
    with pytest.raises(Problem) as error:
        service.basket([{'id': item_id, 'quantity': 1, 'answers': {'clean': 'yes'}}])
    assert error.value.status == 400

@pytest.mark.parametrize('action', [[], {}, None, True])
def test_invalid_action_is_a_client_error(service, action):
    doc = service.create('alice', {'items': [{'id': 'newspaper', 'quantity': 1, 'answers': {'clean': 'yes'}}]}, 'create-key-12345678')
    with pytest.raises(Problem) as error:
        service.act(doc['id'], {'action': action, 'version': 1}, 'action-key-12345678', owner='alice')
    assert error.value.status == 400
