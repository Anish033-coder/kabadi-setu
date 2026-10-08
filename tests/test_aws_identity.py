from unittest.mock import Mock
import pytest
from scripts.aws_identity import require_non_root


def test_root_cannot_reach_mutating_helpers():
    session = Mock()
    session.client.return_value.get_caller_identity.return_value = {'Arn': 'arn:aws:iam::123456789012:root'}
    with pytest.raises(SystemExit, match='Root login detected'):
        require_non_root(session)
    session.client.assert_called_once_with('sts')


def test_assumed_role_session_is_returned():
    session = Mock()
    session.client.return_value.get_caller_identity.return_value = {'Arn': 'arn:aws:sts::123456789012:assumed-role/Developer/session'}
    assert require_non_root(session) is session
