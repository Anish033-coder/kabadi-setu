"""Calculate a four-service subtotal from an isolated flow's recorded usage."""
import argparse
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('scans', 'image_requests', 'api_requests', 'lambda_invocations',
          'lambda_billed_ms', 'ddb_read_units', 'ddb_write_units')


def estimate(counts, prices):
    values = {}
    for field in FIELDS:
        value = counts[field]
        if isinstance(value, bool):
            raise ValueError(f'{field} must be a number')
        value = Decimal(str(value))
        if not value.is_finite() or value < 0:
            raise ValueError(f'{field} must be finite and nonnegative')
        values[field] = value
    if not values['scans'] or values['scans'] != values['scans'].to_integral():
        raise ValueError('scans must be a positive integer')

    def rate(service, usage):
        matches = [p for p in prices[service]['prices'] if p['usage'] == usage and p['beginRange'] == '0']
        if len(matches) != 1:
            raise ValueError(f'Expected one first-tier price for {usage}')
        return Decimal(matches[0]['pricePerUnit']['USD'])

    costs = {
        'rekognition': values['image_requests'] * Decimal('0.00125'),
        'http_api': values['api_requests'] * rate('AmazonApiGateway', 'APS3-ApiGatewayHttpRequest'),
        'lambda': values['lambda_invocations'] * rate('AWSLambda', 'APS3-Request-ARM')
                  + values['lambda_billed_ms'] / 1000 * Decimal('0.5') * rate('AWSLambda', 'APS3-Lambda-GB-Second-ARM'),
        'dynamodb': values['ddb_read_units'] * rate('AmazonDynamoDB', 'APS3-ReadRequestUnits')
                    + values['ddb_write_units'] * rate('AmazonDynamoDB', 'APS3-WriteRequestUnits'),
    }
    total = sum(costs.values())
    return {'currency':'USD', 'basis':'list-price estimate before credits and tax; four-service subtotal',
            'components':{key:str(value) for key,value in costs.items()},
            'sample_subtotal':str(total), 'per_100_scans':str(total / values['scans'] * 100),
            'projection_200000_scans':str(total / values['scans'] * 200000),
            'excludes':['S3', 'logs', 'hosting', 'Cognito', 'bandwidth', 'unreported failed-attempt usage']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('counts', type=Path, help='Private JSON with counts from the same isolated flow/window')
    args = parser.parse_args()
    prices = json.loads((ROOT/'eval/results/infrastructure-mumbai-prices.json').read_text())
    try:
        print(json.dumps(estimate(json.loads(args.counts.read_text()), prices), indent=2))
    except (ValueError, KeyError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
