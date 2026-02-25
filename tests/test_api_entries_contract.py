from __future__ import annotations

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


def test_entries_lifecycle_contract(client) -> None:
    create_payload = {
        "date": "2026-02-20",
        "weight": 72.5,
        "body_fat": 18.2,
        "calories": 2200,
        "steps": 8500,
        "sleep_total": "06:55",
        "sleep_quality": "good",
        "observations": "felt energetic",
    }

    post_res = client.post("/api/entries", json=create_payload)
    assert post_res.status_code == 201
    post_body = post_res.get_json()
    assert post_body == pytest.approx(  # type: ignore[arg-type]
        {
            "success": True,
            "entry": {
                "id": post_body["entry"]["id"],
                "date": "2026-02-20",
                "weight": 72.5,
                "body_fat": 18.2,
                "calories": 2200,
                "training_volume": None,
                "steps": 8500,
                "sleep_total": "06:55",
                "sleep_total_decimal": 6 + (55 / 60),
                "sleep_quality": "good",
                "observations": "felt energetic",
            },
        }
    )

    get_one_res = client.get("/api/entries?date=2026-02-20")
    assert get_one_res.status_code == 200
    get_one_body = get_one_res.get_json()
    assert get_one_body["success"] is True
    assert get_one_body["entry"]["date"] == "2026-02-20"
    assert get_one_body["entry"]["sleep_total"] == "06:55"
    assert get_one_body["entry"]["sleep_total_decimal"] == pytest.approx(6 + (55 / 60))

    update_payload = {
        "date": "2026-02-20",
        "weight": 73.1,
        "sleep_total": "07:30",
        "observations": "updated entry",
    }
    put_res = client.put("/api/entries", json=update_payload)
    assert put_res.status_code == 200
    put_body = put_res.get_json()
    assert put_body["success"] is True
    assert put_body["entry"]["weight"] == 73.1
    assert put_body["entry"]["sleep_total"] == "07:30"
    assert put_body["entry"]["sleep_total_decimal"] == pytest.approx(7.5)
    assert put_body["entry"]["observations"] == "updated entry"

    get_all_res = client.get("/api/entries")
    assert get_all_res.status_code == 200
    get_all_body = get_all_res.get_json()
    assert get_all_body["success"] is True
    assert isinstance(get_all_body["entries"], list)
    assert len(get_all_body["entries"]) == 1
    assert get_all_body["entries"][0]["date"] == "2026-02-20"
    assert get_all_body["entries"][0]["sleep_total"] == "07:30"
    assert get_all_body["entries"][0]["sleep_total_decimal"] == pytest.approx(7.5)


@pytest.mark.parametrize("bad_sleep", [7.5, "24:00", "7:3", "abc"])
def test_entries_sleep_validation_rejects_invalid_values(client, bad_sleep: object) -> None:
    res = client.post(
        "/api/entries",
        json={"date": "2026-02-21", "sleep_total": bad_sleep},
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["success"] is False
    assert body["error"] == "sleep_total must be in HH:MM format"
