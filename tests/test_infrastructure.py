from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock
import os
import yaml
import pytest
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
            if resource == '*':
                assert actions == ['rekognition:DetectLabels'], statement
                assert statement.get('Condition') == {'StringEquals': {'aws:RequestedRegion': 'ap-south-1'}}, statement
                continue
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
        for provider in ['rekognition', 'bedrock']:
            transformed=transform(deepcopy(source),{'RecognitionEnabled':enabled, 'RecognitionProvider':provider},loader)
            assert_scoped(transformed)
            resolved = resolve_conditions(transformed, {'RecognitionEnabled':enabled, 'RecognitionProvider':provider})
            allowed = [s['Action'] for s in statements(resolved)]
            assert ('rekognition:DetectLabels' in allowed) == (enabled == 'true' and provider == 'rekognition')
            assert ('bedrock:InvokeModel' in allowed) == (enabled == 'true' and provider == 'bedrock')

def test_budget_alerts_and_safe_defaults():
    source=yaml_parse((ROOT/'template.yaml').read_text())
    assert source['Parameters']['RecognitionEnabled']['Default']=='false'
    settings=source['Resources']['HttpApi']['Properties']['DefaultRouteSettings']
    assert settings=={'ThrottlingRateLimit':5,'ThrottlingBurstLimit':10}
    budget=yaml_parse((ROOT/'infra/budget.yaml').read_text())
    alerts=budget['Resources']['SpendingBudget']['Properties']['NotificationsWithSubscribers']
    assert sorted(a['Notification']['Threshold'] for a in alerts)==[1,5,10]


@pytest.mark.parametrize('actions', ['rekognition:*', 'rekognition:DetectFaces', ['rekognition:DetectLabels', 's3:GetObject']])
def test_detect_labels_exception_cannot_widen(actions):
    source=yaml_parse((ROOT/'template.yaml').read_text())
    source['Resources']['ApiFunctionRole']['Properties']['Policies'][0]['PolicyDocument']['Statement'].append({
        'Effect':'Allow', 'Action':actions, 'Resource':'*',
        'Condition':{'StringEquals':{'aws:RequestedRegion':'ap-south-1'}},
    })
    with pytest.raises(AssertionError): assert_scoped(source)


def resolve_conditions(template, parameters):
    def resolve(value):
        if isinstance(value, list): return [resolve(v) for v in value]
        if not isinstance(value, dict): return value
        if set(value) == {'Ref'} and value['Ref'] in parameters: return parameters[value['Ref']]
        if set(value) == {'Condition'}: return resolve(template['Conditions'][value['Condition']])
        if set(value) == {'Fn::Equals'}:
            left, right = resolve(value['Fn::Equals'])
            return left == right
        if set(value) == {'Fn::And'}: return all(resolve(value['Fn::And']))
        if set(value) == {'Fn::If'}:
            name, yes, no = value['Fn::If']
            return resolve(yes if resolve(template['Conditions'][name]) else no)
        return {k:resolve(v) for k,v in value.items()}
    return resolve(template)
