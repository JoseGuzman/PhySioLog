from __future__ import annotations

from datetime import date

import pytest

from physiolog import create_app
from physiolog.extensions import db


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTO_CREATE_DB = False
    DEBUG = False
    SECRET_KEY = "test-secret-key"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_stats_success_contract_shape(client) -> None:
    payload = {
        "date": date.today().isoformat(),
        "weight": 72.0,
        "body_fat": 18.0,
        "calories": 2100,
        "steps": 8000,
        "sleep_total": "07:30",
    }
    assert client.post("/api/entries", json=payload).status_code == 201

    res = client.get("/api/stats?window=7d")
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert body["window"] == "7d"
    assert body["window_days"] == 7
    assert isinstance(body["start_date"], str)
    assert isinstance(body["end_date"], str)
    assert isinstance(body["stats"], dict)
    assert "avg_sleep" in body["stats"]
    assert "total_entries" in body["stats"]


def test_stats_rejects_invalid_window_format(client) -> None:
    res = client.get("/api/stats?window=bad")
    assert res.status_code == 400
    body = res.get_json()
    assert body["success"] is False
    assert body["error"] == "format is 7d,30d,3m,1y"


@pytest.mark.parametrize("days_value", [0, -2])
def test_stats_rejects_non_positive_days(client, days_value: int) -> None:
    res = client.get(f"/api/stats?days={days_value}")
    assert res.status_code == 400
    body = res.get_json()
    assert body["success"] is False
    assert body["error"] == "days must be a positive integer"


def test_stats_no_data_returns_contract_error(client) -> None:
    res = client.get("/api/stats")
    assert res.status_code == 404
    body = res.get_json()
    assert body["success"] is False
    assert body["error"] == "No data available"
