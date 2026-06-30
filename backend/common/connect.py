"""WebSocket $connect: stores the connection."""
from datetime import datetime, timezone

from common.db import table, conn_pk


def lambda_handler(event, _ctx):
    cid = event["requestContext"]["connectionId"]
    table.put_item(Item={"PK": conn_pk(cid), "SK": "META", "connectionId": cid, "createdAt": datetime.now(timezone.utc).isoformat()})
    return {"statusCode": 200}
