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

## Migration guide from sqlite to PostgreSQL

1. Backup first (mandatory)

```bash
cd /Users/joseguzman/git/physiolog
cp instance/physiolog.db "instance/physiolog.backup.$(date +%Y-%m-%d_%H:%M:%S).db"
```

and export to SQLite tables to CSV:

```bash
mkdir -p ./tmp/physiolog_migration

sqlite3 -header -csv instance/physiolog.db \
"SELECT id,name,age,height_cm,weight_kg,email,password_hash,is_active_user,is_admin,has_subscription FROM users;" \
> ./tmp/physiolog_migration/users.csv

sqlite3 -header -csv instance/physiolog.db \
"SELECT id,user_id,date,weight,body_fat,calories,training_volume,steps,sleep_total,sleep_quality,observations FROM health_entries;" \
> ./tmp/physiolog_migration/health_entries.csv
```

1. Verify source counts in SQLite

```bash
sqlite3 instance/physiolog.db "SELECT COUNT(*) FROM users;"
sqlite3 instance/physiolog.db "SELECT COUNT(*) FROM health_entries;"
```

1. Prepare staging PostgreSQL database

We create a new PostgreSQL database for staging:

```bash
createdb physiolog_staging
psql -d physiolog_staging -c "SELECT current_database();"
```

The App connection string for stagin should be set to:

```bash
export APP_ENV=staging
export SQLALCHEMY_DATABASE_URI="postgresql+psycopg://${USER}@localhost:5432/physiolog_staging"
export AUTO_CREATE_DB=True
uv run python -c "from physiolog import create_app; create_app()"
export AUTO_CREATE_DB=False
```

Import the CSV files into PostgreSQL:

```bash
psql "postgresql://${USER}@localhost:5432/physiolog_staging" -c "\copy users(id,name,age,height_cm,weight_kg,email,password_hash,is_active_user,is_admin,has_subscription) FROM '/tmp/physiolog_migration/users.csv' CSV HEADER"
psql "postgresql://${USER}@localhost:5432/physiolog_staging" -c "\copy health_entries(id,user_id,date,weight,body_fat,calories,training_volume,steps,sleep_total,sleep_quality,observations) FROM '/tmp/physiolog_migration/health_entries.csv' CSV HEADER"
```

Verify counts in PostgreSQL:

```bash
psql "postgresql://${USER}@localhost:5432/physiolog_staging" -c "SELECT setval(pg_get_serial_sequence('users','id'), COALESCE((SELECT MAX(id) FROM users),1), true);"
psql "postgresql://${USER}@localhost:5432/physiolog_staging" -c "SELECT setval(pg_get_serial_sequence('health_entries','id'), COALESCE((SELECT MAX(id) FROM health_entries),1), true);"

psql "postgresql://${USER}@localhost:5432/physiolog_staging" -c "SELECT COUNT(*) FROM users;"
psql "postgresql://${USER}@localhost:5432/physiolog_staging" -c "SELECT COUNT(*) FROM health_entries;"
```

## Rollback and Restore Procedure

Use this section if migration/import fails or staging behavior is incorrect.

### Rollback triggers (Go/No-Go)

Rollback immediately if any of these are true:

- Source and target row counts do not match.
- Orphan records exist in `health_entries` (`user_id` not found in `users`).
- Login or core API smoke tests fail after migration.

### A) SQLite restore (local dev source)

1. Stop the app if it is running.
2. Restore the latest SQLite backup file:

```bash
cp instance/physiolog.backup.YYYYMMDD_HHMMSS.db instance/physiolog.db
```

3. Verify counts:

```bash
sqlite3 instance/physiolog.db "SELECT COUNT(*) FROM users;"
sqlite3 instance/physiolog.db "SELECT COUNT(*) FROM health_entries;"
```

### B) PostgreSQL backup (before risky changes)

Create a dump before re-importing or applying schema changes:

```bash
pg_dump "postgresql://${USER}@localhost:5432/physiolog_staging" > /tmp/physiolog_staging_prechange.sql
```

### C) PostgreSQL restore (staging)

1. Drop and recreate staging DB:

```bash
dropdb physiolog_staging
createdb physiolog_staging
```

2. Restore from SQL dump:

```bash
psql "postgresql://${USER}@localhost:5432/physiolog_staging" < /tmp/physiolog_staging_prechange.sql
```

3. Validate restore:

```bash
psql "postgresql://${USER}@localhost:5432/physiolog_staging" -c "SELECT COUNT(*) FROM users;"
psql "postgresql://${USER}@localhost:5432/physiolog_staging" -c "SELECT COUNT(*) FROM health_entries;"
psql "postgresql://${USER}@localhost:5432/physiolog_staging" -c "SELECT COUNT(*) FROM health_entries h LEFT JOIN users u ON u.id=h.user_id WHERE u.id IS NULL;"
```

Expected:

- Users count matches source.
- Health entries count matches source.
- Orphan count is `0`.

### D) Re-run migration safely (if needed)

If import failed due to partial data, reset staging first:

```bash
dropdb physiolog_staging
createdb physiolog_staging
```

Then re-run the migration steps from this guide (schema creation, `\copy`, sequence reset, validation).
