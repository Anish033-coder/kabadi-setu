from pathlib import Path
import cedarpy
import pytest
from backend.access import check_access, POLICIES
from backend.domain import Problem

SCHEMA = (Path(__file__).parents[1] / 'policies/access.cedarschema.json').read_text()

def test_cedar_rejects_other_owner():
    with pytest.raises(Problem): check_access({'id':'r','owner':'alice'}, 'household', 'view', 'bob')

def test_cedar_link_cannot_cancel():
    with pytest.raises(Problem): check_access({'id':'r','owner':'alice'}, 'pickup_link', 'cancel')

def test_cedar_accepts_household_and_scoped_link():
    check_access({'id':'r','owner':'alice'}, 'household', 'view', 'alice')
    check_access({'id':'r','owner':'alice'}, 'pickup_link', 'accept')

def test_cedar_household_cannot_answer_its_own_request():
    for action in ('accept', 'reject'):
        with pytest.raises(Problem): check_access({'id':'r','owner':'alice'}, 'household', action, 'alice')

def test_policies_match_schema():
    result = cedarpy.validate_policies(POLICIES, SCHEMA)
    assert result.validation_passed, result.errors
