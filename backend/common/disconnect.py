"""WebSocket $disconnect: removes the connection."""
from common.db import table, conn_pk


def lambda_handler(event, _ctx):
    cid = event["requestContext"]["connectionId"]
    table.delete_item(Key={"PK": conn_pk(cid), "SK": "META"})
    return {"statusCode": 200}
