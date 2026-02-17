"""
openai_services.py

Service functions to verify OpenAI API connectivity from the backend.
No Flask dependencies here (service-layer friendly).
"""

import os

from openai import OpenAI


def run_smoke_test() -> dict:
    """
    test function to verify OpenAI API connectivity from the backend

    Returns:
        dict: _description_
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

    # Responses API (recommended for new integrations)
    response = client.responses.create(
        model="gpt-5.2",
        input="Reply with exactly: OK",
    )

    # usage monitors cost per coach call
    usage_obj = getattr(response, "usage", None)
    # Make usage JSON-serializable
    if usage_obj is None:
        usage = None
    elif hasattr(usage_obj, "model_dump"):
        usage = usage_obj.model_dump()
    else:
        usage = {
            "input_tokens": getattr(usage_obj, "input_tokens", None),
            "output_tokens": getattr(usage_obj, "output_tokens", None),
            "total_tokens": getattr(usage_obj, "total_tokens", None),
        }

    return {
        "ok": True,
        "model": "gpt-5.2",
        "output_text": response.output_text,
        "response_id": getattr(response, "id", None),
        "usage": usage,
    }
