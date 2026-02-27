# PhySioLog Database Testing Guide

Temporaly, the database in instance/physiolog.db, you can see the table for the users and health entries with the following command:
>>> sqlite3 instance/physiolog.db "PRAGMA table_info(health_entries);"
>>> sqlite3 instance/physiolog.db "PRAGMA table_info(users);"

To test in flask shell
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
# check columns
>>> [(u.id, u.name, u.email, u.is_active_user) for u in users]
>>> users # returns a list of users
[<User 1>, <User 2>, <User 3>]
# check entries of User 1
>>> first_user = User.query.order_by(User.id.asc()).first()
>>> (first_user.id, first_user.name, first_user.email)