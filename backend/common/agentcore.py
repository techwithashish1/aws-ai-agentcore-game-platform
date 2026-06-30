"""Helpers for invoking Bedrock AgentCore runtimes and parsing JSON replies."""
import json

import boto3

from common.db import json_dumps

core = boto3.client("bedrock-agentcore")


def invoke_runtime_json(runtime_arn: str, session_id: str, payload: dict) -> dict:
    """Invoke an AgentCore runtime and best-effort parse a JSON object response."""
    resp = core.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        runtimeSessionId=session_id,
        payload=json_dumps(payload).encode(),
    )
    text = _extract_text(resp)
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            start, end = text.index("{"), text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return {}


def _extract_text(obj):
    if obj is None:
        return ""
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj).decode(errors="ignore")
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "read"):
        try:
            return obj.read().decode(errors="ignore")
        except Exception:
            return ""
    if isinstance(obj, dict):
        # common response wrappers in SDK/runtime payloads
        for k in ("payload", "response", "body", "data", "bytes", "text", "output", "result"):
            if k in obj:
                text = _extract_text(obj[k])
                if text:
                    return text
        # Last resort: if this is already the business object, stringify it.
        if any(k in obj for k in ("line", "emotion", "tip", "topic")):
            try:
                return json.dumps(obj)
            except Exception:
                return ""
        return ""
    if isinstance(obj, list):
        for it in obj:
            text = _extract_text(it)
            if text:
                return text
        return ""
    return ""
