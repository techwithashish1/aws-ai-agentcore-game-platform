"""WebSocket push helper."""
import json
from decimal import Decimal

import boto3


class _DecimalEncoder(json.JSONEncoder):
    """Serialize DynamoDB Decimal values to int/float so json.dumps never raises."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj == obj.to_integral_value() else float(obj)
        return super().default(obj)


def push_to_client(endpoint: str, connection_id: str, payload: dict) -> None:
    """Send a JSON payload to a WebSocket connection; ignore stale connections."""
    api = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint)
    try:
        api.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(payload, cls=_DecimalEncoder).encode(),
        )
    except api.exceptions.GoneException:
        pass  # client disconnected
