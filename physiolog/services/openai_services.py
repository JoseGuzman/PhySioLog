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

    return {
        "ok": True,
        "model": "gpt-5.2",
        "output_text": response.output_text,
        "response_id": getattr(response, "id", None),
    }
