from __future__ import annotations

from datetime import date

import pytest

from physiolog import create_app
from physiolog.extensions import db
from physiolog.models import AdminClientAssignment, HealthEntry, User


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


def _create_user(email: str, password: str, *, is_admin: bool = False) -> User:
    user = User(email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def _login(client, email: str, password: str) -> None:
    res = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    assert res.status_code in (302, 303)


def test_select_client_marks_single_selected_user(client, app) -> None:
    with app.app_context():
        admin = _create_user("admin@example.com", "pw", is_admin=True)
        client_one = _create_user("one@example.com", "pw")
        client_two = _create_user("two@example.com", "pw")

        db.session.add_all(
            [
                AdminClientAssignment(
                    admin_user_id=admin.id,
                    client_user_id=client_one.id,
                ),
                AdminClientAssignment(
                    admin_user_id=admin.id,
                    client_user_id=client_two.id,
                ),
            ]
        )
        db.session.commit()
        client_two_id = client_two.id

    _login(client, "admin@example.com", "pw")

    res = client.post(
        f"/admin/clients/{client_two_id}/select",
        data={"status": "active"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert f'value="{client_two_id}" checked' in body


def test_selected_client_drives_read_only_data_apis(client, app) -> None:
    with app.app_context():
        admin = _create_user("admin@example.com", "pw", is_admin=True)
        selected_client = _create_user("client@example.com", "pw")
        selected_client.age = 42
        selected_client.height_cm = 180
        selected_client.weight_kg = 81.5

        db.session.add(
            AdminClientAssignment(
                admin_user_id=admin.id,
                client_user_id=selected_client.id,
            )
        )
        db.session.add(
            HealthEntry(
                user_id=selected_client.id,
                date=date(2026, 3, 1),
                weight_kg=81.5,
                sleep_hours=7.0,
            )
        )
        db.session.commit()
        selected_client_id = selected_client.id

    _login(client, "admin@example.com", "pw")

    select_res = client.post(
        f"/admin/clients/{selected_client_id}/select",
        data={},
        follow_redirects=False,
    )
    assert select_res.status_code in (302, 303)

    profile_res = client.get("/api/user-profile")
    assert profile_res.status_code == 200
    profile_body = profile_res.get_json()
    assert profile_body["profile"]["age"] == 42
    assert profile_body["profile"]["height_cm"] == 180
    assert profile_body["profile"]["weight_kg"] == 81.5

    entries_res = client.get("/api/entries")
    assert entries_res.status_code == 200
    entries_body = entries_res.get_json()
    assert len(entries_body["entries"]) == 1
    assert entries_body["entries"][0]["date"] == "2026-03-01"

    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    stats_body = stats_res.get_json()
    assert stats_body["stats"]["total_entries"] == 1
