# PostgreSQL Migration Guide (Staging)

This guide migrates data from `sqlite3` (`instance/physiolog.db`) to PostgreSQL staging (`physiolog_staging`) and avoids duplicate key conflicts.

## Why duplicate key errors happen

If staging already contains rows, importing CSV files with explicit `id` values can fail with errors like:

- `duplicate key value violates unique constraint "users_pkey"`
- `duplicate key value violates unique constraint "health_entries_pkey"`

## Safe reset-and-import flow (staging)

Run from repo root:

```bash
export PSQL_URI="postgresql://${USER}@localhost:5432/physiolog_staging"

# 0) confirm current rows
psql "$PSQL_URI" -c "SELECT COUNT(*) FROM users;"
psql "$PSQL_URI" -c "SELECT COUNT(*) FROM health_entries;"

# 1) clear staging tables (staging only)
psql "$PSQL_URI" -c "TRUNCATE TABLE health_entries, users RESTART IDENTITY CASCADE;"

# 2) import users first, then entries (use actual file path)
psql "$PSQL_URI" -c "\copy users(id,name,age,height_cm,weight_kg,email,password_hash,is_active_user,is_admin,has_subscription) FROM './tmp/physiolog_migration/users.csv' CSV HEADER"
psql "$PSQL_URI" -c "\copy health_entries(id,user_id,date,weight_kg,body_fat_percent,calories_kcal,training_volume_kg,steps_count,sleep_hours,sleep_quality,observations,protein_g) FROM './tmp/physiolog_migration/health_entries.csv' CSV HEADER"

# 3) sequence fix after explicit IDs
psql "$PSQL_URI" -c "SELECT setval(pg_get_serial_sequence('users','id'), COALESCE((SELECT MAX(id) FROM users),1), true);"
psql "$PSQL_URI" -c "SELECT setval(pg_get_serial_sequence('health_entries','id'), COALESCE((SELECT MAX(id) FROM health_entries),1), true);"

# 4) validate
psql "$PSQL_URI" -c "SELECT COUNT(*) FROM users;"
psql "$PSQL_URI" -c "SELECT COUNT(*) FROM health_entries;"
```

## Notes

- Import order matters: `users` first, then `health_entries` (foreign key dependency).
- Path must match where CSVs were created:
  - If exported to `./tmp/physiolog_migration/...`, import from `./tmp/...`.
  - If exported to `/tmp/physiolog_migration/...`, import from `/tmp/...`.
- `TRUNCATE ... RESTART IDENTITY` is intended for staging reset, not production.
