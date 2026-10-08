import pytest
from backend.access import check_access
from backend.domain import Problem

def test_cedar_rejects_other_owner():
    with pytest.raises(Problem): check_access({'id':'r','owner':'alice'}, 'household', 'view', 'bob')

def test_cedar_link_cannot_cancel():
    with pytest.raises(Problem): check_access({'id':'r','owner':'alice'}, 'pickup_link', 'cancel')

def test_cedar_accepts_household_and_scoped_link():
    check_access({'id':'r','owner':'alice'}, 'household', 'view', 'alice')
    check_access({'id':'r','owner':'alice'}, 'pickup_link', 'accept')
