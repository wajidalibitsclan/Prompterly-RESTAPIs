# Backup Restore Test Runbook

> Security Standard §6 — periodic verification that backups produced by
> `app.workers.backup` are functional and restorable. **Until a restore has
> succeeded, you do not have a backup.**

## Cadence

| Type | Frequency | Owner |
|------|-----------|-------|
| Smoke restore (latest daily backup → throwaway container, schema-only check) | **Weekly** | On-call engineer |
| Full restore drill (random daily backup, full data verification, row counts) | **Monthly** | Platform team |
| Disaster-recovery drill (keyring + backup → fresh host, full app boots) | **Quarterly** | Platform team + SRE |

Schedule the smoke restore as a cron job; record the monthly/quarterly drills
in the platform team's calendar with a 30-minute slot.

## Prerequisites

- AWS credentials with read access to the backup bucket
- Docker installed locally (or a throwaway VM)
- The MySQL keyring tarball for the same date as the backup being restored
  (see `DOCKER_DEPLOYMENT_GUIDE.md` — TDE-encrypted tablespaces are
  unrecoverable without it)

## Weekly Smoke Restore

The goal is to prove the latest backup is well-formed and contains data,
**not** to validate every row. Should take under 10 minutes.

```bash
# 1. Pick the most recent daily backup
aws s3 ls s3://$S3_BUCKET_NAME/backups/daily/ | sort | tail -1
BACKUP=prompterly_backup_YYYYMMDD_HHMMSS.sql.gz

# 2. Download
aws s3 cp s3://$S3_BUCKET_NAME/backups/daily/$BACKUP ./

# 3. Spin up a throwaway MySQL
docker run -d --name restore-test \
  -e MYSQL_ROOT_PASSWORD=test \
  -e MYSQL_DATABASE=restore_test \
  -p 13306:3306 mysql:8.0
sleep 20  # wait for mysqld to be ready

# 4. Restore
gunzip -c $BACKUP | docker exec -i restore-test \
  mysql -uroot -ptest restore_test

# 5. Sanity check — every table should have a row count
docker exec restore-test mysql -uroot -ptest restore_test -e "
  SELECT TABLE_NAME, TABLE_ROWS
  FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = 'restore_test'
  ORDER BY TABLE_ROWS DESC;"

# 6. Tear down
docker rm -f restore-test
rm $BACKUP
```

**Pass criteria:** restore completes without error, `users`, `chat_threads`,
`lounges` all return non-zero `TABLE_ROWS`.

**On failure:** stop. Page the platform on-call. Do not delete the failed
backup; it's evidence. Open an incident ticket with the
`mysqldump`/`mysql` stderr attached.

## Monthly Full Restore Drill

Pick a backup from a random day in the last 30. In addition to the smoke
steps above:

```sql
-- Verify recent activity exists (replace date with the backup's date)
SELECT COUNT(*) FROM chat_messages
  WHERE created_at > DATE_SUB(:backup_date, INTERVAL 1 DAY);

-- Verify encryption is intact on restored TDE tables
SELECT TABLE_NAME, CREATE_OPTIONS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'restore_test'
  AND CREATE_OPTIONS LIKE '%ENCRYPTION%';

-- Spot-check that app-layer encryption survives (this row should NOT
-- be human-readable plaintext — it should be a base64 ciphertext blob)
SELECT id, LEFT(content_encrypted, 60) FROM chat_messages LIMIT 1;
```

**Pass criteria:** recent rows exist, TDE encryption flag preserved,
app-layer ciphertext columns still look like ciphertext.

## Quarterly DR Drill

Goal: prove the system is recoverable on fresh infrastructure if production
is destroyed.

1. Provision a fresh host (different region or different cloud account).
2. Restore the keyring tarball from its separate vault to `mysql_keyring`.
3. Restore the latest monthly backup to `mysql_data`.
4. Bring up `docker compose -f docker-compose.prod.yml up -d`.
5. Hit `GET /health` — expect 200.
6. Log in as a known test account; confirm chat history decrypts and
   renders.
7. Tear down. Record duration in the DR-drill log.

**Pass criteria:** the application boots and a real user account's
encrypted content decrypts end-to-end. Total restore time recorded —
this is your RTO baseline.

## Sign-off

After each drill, append a line to `deployment/restore-drills.log`:

```
2026-05-26  weekly-smoke   PASS   8m   alice@prompterly
2026-06-01  monthly-full   PASS  42m   bob@prompterly
2026-06-15  quarterly-dr   FAIL  --    carol@prompterly  (see INC-204)
```

A failed drill is an incident — see `incident-response` runbook (TODO).
