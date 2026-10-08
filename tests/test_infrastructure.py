from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock
import os
import yaml
from samtranslator.yaml_helper import yaml_parse
from samtranslator.translator.transform import transform
from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader

ROOT=Path(__file__).parents[1]

def statements(value):
    if isinstance(value,dict):
        if 'Effect' in value and 'Action' in value: yield value
        for item in value.values(): yield from statements(item)
    elif isinstance(value,list):
        for item in value: yield from statements(item)

def assert_scoped(template):
    for statement in statements(template):
        actions=statement['Action']
        if isinstance(actions,str): actions=[actions]
        assert all('*' not in action for action in actions), statement
        if 'Resource' not in statement: continue # Role trust policy has no Resource.
        resources=statement['Resource']
        if not isinstance(resources,list): resources=[resources]
        for resource in resources:
            assert resource != '*'
            encoded=str(resource)
            if '*' in encoded:
                # Only this bucket's generated object keys may vary. Log-group GetAtt
                # resolves to its stream-scoped ARN, not every log group in the account.
                assert resource == {'Fn::Sub':'${PhotoBucket.Arn}/photos/*'}, resource
    role=template['Resources']['ApiFunctionRole']['Properties']
    assert not role.get('ManagedPolicyArns'), 'Managed policies hide permissions from this check'

def test_source_and_transformed_iam_are_scoped(monkeypatch):
    monkeypatch.setenv('AWS_DEFAULT_REGION','ap-south-1')
    source=yaml_parse((ROOT/'template.yaml').read_text())
    assert_scoped(source)
    # SAM's packaging step normally replaces this local path with an S3 artifact.
    source['Resources']['ApiFunction']['Properties']['CodeUri']='s3://test-artifact-bucket/code.zip'
    loader=ManagedPolicyLoader(Mock())
    for enabled in ['true','false']:
        transformed=transform(deepcopy(source),{'RecognitionEnabled':enabled},loader)
        assert_scoped(transformed)

def test_budget_alerts_and_safe_defaults():
    source=yaml_parse((ROOT/'template.yaml').read_text())
    assert source['Parameters']['RecognitionEnabled']['Default']=='false'
    settings=source['Resources']['HttpApi']['Properties']['DefaultRouteSettings']
    assert settings=={'ThrottlingRateLimit':5,'ThrottlingBurstLimit':10}
    budget=yaml_parse((ROOT/'infra/budget.yaml').read_text())
    alerts=budget['Resources']['SpendingBudget']['Properties']['NotificationsWithSubscribers']
    assert sorted(a['Notification']['Threshold'] for a in alerts)==[1,5,10]
