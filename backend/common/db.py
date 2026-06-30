"""Shared DynamoDB + EventBridge helpers for all lambdas."""
import json
import os
from decimal import Decimal

import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
EVENT_BUS = os.environ.get("EVENT_BUS", "")

table = boto3.resource("dynamodb").Table(TABLE_NAME)
events = boto3.client("events")


def _json_default(obj):
    """Make DynamoDB Decimal values JSON-serializable (int when whole, else float)."""
    if isinstance(obj, Decimal):
        return int(obj) if obj == obj.to_integral_value() else float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def json_dumps(obj) -> str:
    """json.dumps that tolerates DynamoDB Decimal values."""
    return json.dumps(obj, default=_json_default)


def match_pk(match_id: str) -> str:
    return f"MATCH#{match_id}"


def conn_pk(connection_id: str) -> str:
    return f"CONN#{connection_id}"
