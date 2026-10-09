import json
from decimal import Decimal
import pytest
from scripts.estimate_scan_cost import ROOT, estimate


def test_manual_has_zero_ai_and_transaction_units_are_not_doubled():
    prices = json.loads((ROOT/'eval/results/infrastructure-mumbai-prices.json').read_text())
    counts = dict(scans=1,image_requests=0,api_requests=1,lambda_invocations=1,
                  lambda_billed_ms=100,ddb_read_units=1,ddb_write_units=6)
    result = estimate(counts, prices)
    assert Decimal(result['components']['rekognition']) == 0
    assert Decimal(result['components']['dynamodb']) == Decimal('0.0000044025')
    assert Decimal(result['per_100_scans']) == Decimal(result['sample_subtotal']) * 100
    for bad in [0, -1, True, 'NaN']:
        with pytest.raises(ValueError):
            estimate({**counts, 'scans':bad}, prices)
