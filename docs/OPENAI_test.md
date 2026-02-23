# OpenAI Integration Testing

This file contains relevant information to test/execute the OpenAI
integration in Physiolog

## Smoke Test Endpoint

### Basic Command

```bash
curl -s http://localhost:5000/api/llm-smoke | python -m json.tool
```
The python -m json.tool validates it's JSON and prints formatted version.

### Response Example

```json
{
    "API": "b7YA",
    "model": "gpt-5.2",
    "ok": true,
    "output_text": "OK",
    "response_id": "resp_04606bcd69a35e1500699af22be524819ca90eee8c758cee51",
    "usage": {
        "input_tokens": 11,
        "input_tokens_details": {
            "cached_tokens": 0
        },
        "output_tokens": 5,
        "output_tokens_details": {
            "reasoning_tokens": 0
        },
        "total_tokens": 16
    }
}
```

### What This Does

The `/api/llm-smoke` endpoint is a **lightweight health check** for the OpenAI API integration. It:

1. Verifies that the OpenAI service is properly configured and accessible
2. Makes a minimal API call to test authentication and connectivity
3. Returns metadata about the response (model used, response ID, status)
4. Returns `"ok": true` if the integration is working, `false` otherwise

**Use cases:**

- Verify OpenAI credentials are valid before running heavy operations
- Debug connection issues with OpenAI service
- Monitor API availability during deployment/startup

---

## Request/Response Flow (Architecture)

Here's how a GET request flows through the application:

```
┌─────────────────────────────────────────────────────────────────┐
│ Client (Browser / curl)                                         │
│                                                                 │
│  GET http://localhost:5000/api/llm-smoke                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Flask Route Handler (routes_api.py)                             │
│                                                                 │
│  @api_bp.route("/llm-smoke", methods=["GET"])                   │
│  def llm_smoke():                                               │
│      # 1. Request arrives here                                  │
│      # 2. Route handler receives the request                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Service Layer (services/openai_service.py)                      │
│                                                                 │
│  def smoke_test():                                              │
│      # 3. Route calls the service function                      │
│      # 4. Service encapsulates business logic:                  │
│      #    - Initialize OpenAI client                            │
│      #    - Make API call                                       │
│      #    - Parse response                                      │
│      # 5. Service returns structured data (dict)                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Flask Route Handler (routes_api.py)                             │
│                                                                 │
│  return jsonify(result)                                         │
│  # 6. Route converts dict to JSON response                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ HTTP Response (JSON)                                            │
│                                                                 │
│  {                                                              │
│    "model": "gpt-5.2",                                          │
│    "ok": true,                                                  │
│    "output_text": "OK",                                         │
│    "response_id": "resp_..."                                    │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Steps

| Step | Layer | What Happens |
|------|-------|--------------|
| 1 | Client | Browser/curl sends GET request to `/api/llm-smoke` |
| 2 | routes_api.py | Flask matches route and calls handler function |
| 3 | routes_api.py | Handler function imports and calls service function |
| 4 | services/openai_service.py | Service function contains the actual business logic (OpenAI API call) |
| 5 | services/openai_service.py | Service processes the response and returns a Python dictionary |
| 6 | routes_api.py | Handler receives dict and returns `jsonify()` to convert to JSON |
| 7 | Client | Browser/curl receives JSON response |

### Why This Structure?

**Separation of Concerns:**

- **routes_api.py** = HTTP handling (request/response, status codes)
- **services/openai_service.py** = Business logic (what data to fetch, how to process it)

**Benefits:**

- Easy to test services independently (no Flask needed)
- Reusable across multiple endpoints
- Easy to swap implementations (e.g., switch OpenAI providers)
- Services can be used in scripts, background tasks, or notebooks

---

## Example Implementation

### Service Layer (services/openai_service.py)

```python
import os
from openai import OpenAI

def smoke_test() -> dict:
    """Test OpenAI API connectivity."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "say OK"}],
            max_tokens=10
        )
        
        return {
            "ok": True,
            "model": response.model,
            "output_text": response.choices[0].message.content,
            "response_id": response.id
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }
```

### Route Layer (routes_api.py)

```python
from flask import Blueprint, jsonify
from .services.openai_service import smoke_test

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/llm-smoke", methods=["GET"])
def llm_smoke():
    """Health check for OpenAI integration."""
    result = smoke_test()
    return jsonify(result)
```

---

## Testing

```bash
# Test locally
curl -s http://localhost:5000/api/llm-smoke | python -m json.tool

# Pretty-print the response
curl -s http://localhost:5000/api/llm-smoke | json_pp

# Check HTTP status code
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/llm-smoke
```
