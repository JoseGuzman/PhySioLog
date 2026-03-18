# PostgreSQL System-to-System Migration Guide

This guide explains how to move a PostgreSQL database from one system to another, for example from one computer to a different computer, using a logical backup and restore flow.

This is the recommended approach for PhysioLog because it is portable, works across environments, and avoids raw database file copying.

## When to use this guide

Use this guide when:

- The source database is already PostgreSQL
- The target database is also PostgreSQL
- You want to move schema and data safely between systems
- You want a repeatable process that fits Docker and AWS deployment practices

Do not use this guide for SQLite-to-PostgreSQL migration. That is a separate workflow.

## Migration strategy

The migration uses:

1. `pg_dump` on the source system
2. Secure transfer of the dump file to the target system
3. `createdb` on the target system
4. `pg_restore` or `psql` on the target system
5. Validation checks after restore

Prefer a logical dump over copying PostgreSQL data directories directly. Directory-level copying is version-sensitive and much more fragile across machines.

## Prerequisites

Before starting, confirm:

- PostgreSQL client tools are installed on both systems
- You can connect to the source database with `psql`
- You can connect to the target PostgreSQL server with `psql`
- You have credentials to create or restore into the target database
- The source and target PostgreSQL server versions are compatible

Check local client-tool versions:

```bash
psql --version
pg_dump --version
pg_restore --version
```

Check the actual database server versions:

```bash
psql -h "$SOURCE_HOST" -p "$SOURCE_PORT" -U "$SOURCE_USER" -d "$SOURCE_DB" -c "SELECT version();"
psql -h "$TARGET_HOST" -p "$TARGET_PORT" -U "$TARGET_USER" -d postgres -c "SELECT version();"
```

For PhysioLog, a logical migration from PostgreSQL `16.x` to `18.x` is a valid direction. Avoid relying on local CLI version output alone when deciding migration compatibility.

## Variables used in this guide

Replace these placeholders with your actual values:

```bash
SOURCE_HOST=source-host
SOURCE_PORT=5432
SOURCE_DB=physiolog
SOURCE_USER=source_user

TARGET_HOST=target-host
TARGET_PORT=5432
TARGET_DB=physiolog
TARGET_USER=target_user

DUMP_FILE=physiolog_$(date +%Y-%m-%d_%H-%M-%S).dump
```

## Step 1: Inspect the source database

Before exporting, confirm the source database server version and capture a few baseline values.

Connect to the source database:

```bash
psql -h "$SOURCE_HOST" -p "$SOURCE_PORT" -U "$SOURCE_USER" -d "$SOURCE_DB"
```

Run a few checks:

```sql
SELECT current_database();
SELECT version();
```

If helpful, record row counts for important tables:

```sql
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM health_entries;
```

## Step 2: Create a backup on the source system

Create a logical dump using PostgreSQL custom format:

```bash
pg_dump \
  -Fc \
  -h "$SOURCE_HOST" \
  -p "$SOURCE_PORT" \
  -U "$SOURCE_USER" \
  -d "$SOURCE_DB" \
  -f "$DUMP_FILE"
```

Why `-Fc`:

- Better restore flexibility
- Supports selective restore if needed
- Works well with `pg_restore`

Confirm the dump file exists:

```bash
ls -lh "$DUMP_FILE"
```

## Step 3: Transfer the dump file to the target system

Use `scp` or another secure transfer method.

Example:

```bash
scp "$DUMP_FILE" your-user@target-machine:/tmp/
```

After transfer, confirm the file exists on the target machine:

```bash
ls -lh /tmp/"$DUMP_FILE"
```

## Step 4: Create the target database

On the target system, create an empty database.

```bash
createdb \
  -h "$TARGET_HOST" \
  -p "$TARGET_PORT" \
  -U "$TARGET_USER" \
  "$TARGET_DB"
```

Verify it exists:

```bash
psql -h "$TARGET_HOST" -p "$TARGET_PORT" -U "$TARGET_USER" -d "$TARGET_DB" -c "SELECT current_database();"
```

## Step 5: Restore the dump into the target database

Restore with `pg_restore`:

```bash
pg_restore \
  -h "$TARGET_HOST" \
  -p "$TARGET_PORT" \
  -U "$TARGET_USER" \
  -d "$TARGET_DB" \
  --clean \
  --if-exists \
  --no-owner \
  /tmp/"$DUMP_FILE"
```

Notes:

- `--clean` drops existing objects before recreating them
- `--if-exists` makes drop operations safer
- `--no-owner` avoids restore failures when the source owner role does not exist on the target system
- Only use this against a database you are prepared to overwrite

If the target database must remain untouched until cutover, restore into a newly created staging or temporary database first.

If you want to preserve source ownership exactly, create the required roles on the target before restore and omit `--no-owner`.

## Step 6: Validate the migrated database

Connect to the target database:

```bash
psql -h "$TARGET_HOST" -p "$TARGET_PORT" -U "$TARGET_USER" -d "$TARGET_DB"
```

Run validation checks:

```sql
SELECT current_database();
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM health_entries;
```

Check the tables exist:

```sql
\dt
```

If your schema uses sequences, verify inserts still work correctly after restore.

## Step 7: Point PhysioLog to the new database

Update the application environment variables to use the target PostgreSQL database.

Example SQLAlchemy connection string:

```bash
export APP_ENV=staging
export SQLALCHEMY_DATABASE_URI="postgresql+psycopg://${TARGET_USER}@${TARGET_HOST}:${TARGET_PORT}/${TARGET_DB}"
```

Then start the app and test core behavior.

## Step 8: Smoke test the application

After switching the connection string, verify:

- App startup succeeds
- Login works
- `/api/entries` returns expected data
- `/api/stats` returns expected calculations
- No obvious 500 errors appear in logs

## Recommended validation checklist

Use this as a quick go/no-go check:

- Source and target row counts match for key tables
- Core tables exist in the target database
- App starts successfully against target PostgreSQL
- Core API endpoints respond correctly
- New inserts work correctly
- No missing extensions or permission errors appear

## Rollback plan

If the target restore fails or app behavior is incorrect:

1. Keep the original source database unchanged
2. Revert the app connection string to the old database
3. Drop and recreate the target database if needed
4. Repeat restore after fixing the issue

If you are restoring into an already used target database, create a backup first:

```bash
pg_dump \
  -Fc \
  -h "$TARGET_HOST" \
  -p "$TARGET_PORT" \
  -U "$TARGET_USER" \
  -d "$TARGET_DB" \
  -f target_pre_restore.dump
```

## Important cautions

- Do not copy PostgreSQL internal data files directly between machines
- Do not restore into the wrong database when using `--clean`
- Use `localhost` explicitly if a host shell variable is unset; otherwise PostgreSQL may fall back to a local socket unexpectedly
- Ensure the target PostgreSQL server is running before `createdb` or `pg_restore`
- Ensure roles and permissions exist on the target system, or restore with `--no-owner`
- If extensions are required, install them on the target before restore
- If PostgreSQL major versions differ significantly, validate compatibility using the server versions, not only the local client-tool versions

## Example end-to-end summary

Source system:

```bash
pg_dump -Fc -h localhost -p 5432 -U jose -d physiolog -f physiolog.dump
scp physiolog.dump jose@target-machine:/tmp/
```

Target system:

```bash
createdb -h localhost -p 5432 -U jose physiolog
pg_restore -h localhost -p 5432 -U jose -d physiolog --clean --if-exists /tmp/physiolog.dump
psql -h localhost -p 5432 -U jose -d physiolog -c "SELECT COUNT(*) FROM users;"
psql -h localhost -p 5432 -U jose -d physiolog -c "SELECT COUNT(*) FROM health_entries;"
```
