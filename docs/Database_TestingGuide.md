# PhySioLog Database Testing Guide

Temporaly, the database in instance/physiolog.db, you can see the table for the users and health entries with the following command:

```bash
>>> sqlite3 instance/physiolog.db "PRAGMA table_info(health_entries);"
>>> sqlite3 instance/physiolog.db "PRAGMA table_info(users);"
```

## Flask Shell Testing

To test in flask shell

```bash
>>> uv run python -m flask shell
Python 3.12.12 (main, Jan 27 2026, 23:31:45) [Clang 21.1.4 ] on darwin
App: physiolog
Instance: /path/to/repo/instance
>>> app
>>> <Flask 'physiolog'>
>>> db
>>> <SQLAlchemy sqlite:////path/to/repo/instance/physiolog.db>
>>> User
>>> User <class 'physiolog.models.User'>
>>> users = User.query.all()
```

We can test the users table entries with the following commands:

```bash
>>> [(u.id, u.name, u.email, u.is_active_user) for u in users]
>>> users # returns a list of users
[<User 1>, <User 2>, <User 3>]
```

To get the first user in the users table:

```bash
>>> first_user = User.query.order_by(User.id.asc()).first()
>>> (first_user.id, first_user.name, first_user.email)
```

## Demo user creation

Import script demo user password (.env)
>>> DEMO_USER_PASSWORD="your-password"
The import script reads DEMO_USER_PASSWORD from .env (or environment) when
creating <demo@physiolog.com>. CLI --password overrides it; otherwise it will prompt.

## Add a new column to users table

If we want to add a boolean column `is_admin` to the users table, we can do it with the following commands in flask shell:

```bash
>>> from sqlalchemy import inspect, text
>>> from physiolog.extensions import db
>>> inspector = inspect(db.engine)
>>> cols = {c["name"] for c in inspector.get_columns("users")}
>>> cols
{'height_cm', 'password_hash', 'email', 'id', 'name', 'age', 'weight_kg', 'is_active_user'}
```

We use SQL syntax to alter the table and add the new column:

```bash
>>> db.session.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"))
```

test the new column is added and has the default value:

```bash
<sqlalchemy.engine.cursor.CursorResult object at 0x112ac2120>
>>> inspector = inspect(db.engine)
>>> cols = {c["name"] for c in inspector.get_columns("users")}
>>> cols
{'height_cm', 'password_hash', 'email', 'id', 'name', 'has_subscription', 'age', 'weight_kg', 'is_active_user', 'is_admin'}
```

We can update a user to be an admin with the following commands:

```bash
>>> u = User.query.filter_by(email='admin@example.com').first()
>>> u.name
'Administrator'
>>> u.is_admin=True
>>> db.session.commit()
>>> exit()
```
