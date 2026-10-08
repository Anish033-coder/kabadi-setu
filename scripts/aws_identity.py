"""Refuse project mutations with the root identity. This check itself is read-only."""
import boto3


def require_non_root(session=None):
    session = session or boto3.Session()
    identity = session.client('sts').get_caller_identity()
    if identity['Arn'].endswith(':root'):
        raise SystemExit('Root login detected. Use a non-root AWS profile before deploying or calling a model.')
    return session


if __name__ == '__main__':
    require_non_root()
    print('Non-root AWS session verified. No resources changed.')
