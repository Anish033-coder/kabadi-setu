"""Create the link secret once, without putting its value in shell arguments or logs."""
import secrets
from aws_identity import require_non_root

session = require_non_root()
session.client('ssm', region_name='ap-south-1').put_parameter(
    Name='/kabadi-setu/link-secret', Type='SecureString', Value=secrets.token_hex(32), Overwrite=False)
print('Link secret created. Its value has not been printed.')
