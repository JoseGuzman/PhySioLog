from __future__ import annotations

import pytest

from physiolog import create_app
from physiolog.extensions import db
from physiolog.models import AdminClientAssignment, User


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


def test_admin_clients_page_shows_only_assigned_users(client, app) -> None:
    with app.app_context():
        admin = _create_user("admin@example.com", "pw", is_admin=True)
        visible_client = _create_user("visible@example.com", "pw")
        hidden_client = _create_user("hidden@example.com", "pw")

        db.session.add(
            AdminClientAssignment(
                admin_user_id=admin.id,
                client_user_id=visible_client.id,
            )
        )
        db.session.commit()

    _login(client, "admin@example.com", "pw")

    res = client.get("/admin")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "visible@example.com" in body
    assert "hidden@example.com" not in body


def test_admin_cannot_update_unassigned_user_subscription(client, app) -> None:
    with app.app_context():
        admin = _create_user("admin@example.com", "pw", is_admin=True)
        assigned_client = _create_user("assigned@example.com", "pw")
        other_client = _create_user("other@example.com", "pw")

        db.session.add(
            AdminClientAssignment(
                admin_user_id=admin.id,
                client_user_id=assigned_client.id,
            )
        )
        db.session.commit()
        other_client_id = other_client.id

    _login(client, "admin@example.com", "pw")

    res = client.post(
        f"/admin/clients/{other_client_id}/subscription",
        data={"status": "active"},
        follow_redirects=False,
    )
    assert res.status_code == 404
