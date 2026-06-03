# Incident Response Runbook

> Security Standard §13. This is the procedure for responding to a confirmed
> or suspected security incident affecting Prompterly user data or systems.
>
> **GDPR notification clock starts the moment a personal-data breach is
> confirmed and runs for 72 hours.** Don't wait for full root cause before
> starting the notification track in parallel.

## Severity tiers

| Tier | Definition | Examples | Page on-call? |
|------|------------|----------|---------------|
| **SEV-1** | Confirmed unauthorised access to personal data, encrypted at-rest content, or production credentials | Stolen KMS key, leaked DB dump, attacker session in admin panel | Yes — immediately |
| **SEV-2** | Suspected access OR confirmed access to a narrowly scoped non-PII system | Webhook abuse, single user account takeover, exposed staging env | Yes — within 30 min |
| **SEV-3** | Detected attempt without confirmed compromise | Repeated 401s from one IP, malformed Stripe signatures, scraper | No — handle async |
| **SEV-4** | Hygiene finding from an audit, pentest, or scanner | New CVE in a dependency, missing security header | No — open a ticket |

When in doubt, classify **up** for the first hour. Downgrading is cheap; missing the 72-hour window is not.

## Roles

| Role | Owner | Responsibility |
|------|-------|----------------|
| Incident Commander (IC) | First responder, hands off if needed | Owns the timeline, calls SEV, decides containment vs. preservation |
| Comms Lead | Founder / designated comms | External notifications (users, OAIC, partners) — see Notification section |
| Tech Lead | Senior engineer on duty | Containment + investigation; coordinates with IC |
| Scribe | Anyone not in the above roles | Maintains the incident doc in real time |

One person can hold multiple roles for a SEV-3 or below. Never combine IC and Tech Lead for a SEV-1.

## Phase 1 — Detect & classify (first 15 minutes)

1. Open an incident doc — title `INC-YYYY-MM-DD-<slug>`. Start a running timeline with timestamps; every action gets a line.
2. Assign IC, Tech Lead, Comms Lead, Scribe (see above).
3. Classify the severity using the table above. **Write it down**, even tentatively.
4. For SEV-1 / SEV-2: page on-call via the escalation list (see bottom).
5. Decide preservation vs. containment posture:
   - **Preserve** = collect evidence before changing state. Required for any tier where prosecution or insurance claim is plausible.
   - **Contain** = stop the bleed first. Required when active exfiltration is suspected.
   - Default to **contain first** for SEV-1 unless legal advises otherwise.

## Phase 2 — Contain (first hour)

Pick the smallest action that stops the bleed:

| Symptom | Containment action |
|---------|-------------------|
| Compromised user session/token | Revoke `UserSession` rows for the user; rotate JWT secret if scoped beyond one user (forces global re-login) |
| Compromised admin account | Disable account, force-rotate the admin's password + 2FA, audit `audit_logs` for actions taken by their `user_id` |
| Stolen API key (OpenAI / Anthropic / Stripe / KMS) | Rotate via the provider console immediately; update AWS Secrets Manager; rolling-restart the API containers |
| Production DB credentials leak | Rotate `MYSQL_ROOT_PASSWORD` and the app's DB user; force-restart the api + worker containers |
| Active attacker session in `/admin/*` | Disable the admin account; if multi-admin compromise suspected, set `is_2fa_enabled=true` enforcement (already required by `get_current_admin_mfa`) and re-issue 2FA to the rest |
| Suspected DB exfiltration | Take a forensic snapshot (point-in-time read replica, NOT a `mysqldump` over the wire); rotate the KMS master key per `app/core/kms.py` rotation runbook |
| Webhook replay storm | Tighten `STRIPE_WEBHOOK_SECRET`; verify `processed_stripe_events` is rejecting duplicates as designed |

Once contained, snapshot relevant state before any cleanup: `audit_logs` for the time window, application logs from `/var/log/prompterly/`, S3 access logs for the backup bucket.

## Phase 3 — Investigate

Goal: answer **scope** (what data) and **dwell time** (how long).

Where to look:

- **`audit_logs` table** — all critical actions for the last 12 months (Security Standard §9). Filter by the suspected user_uuid or admin id.
- **`processed_stripe_events` table** — proves which Stripe events we acted on, in what order.
- **Application logs** at the JSON sink (60-day retention). Grep by `request_id` to reconstruct a request flow.
- **Nginx access logs** at the edge container.
- **AWS CloudTrail** — for any change to the KMS master key, S3 backup bucket, or IAM.
- **Sentry** — for any unhandled exceptions in the relevant window.

For data-impact scope, do NOT decrypt content blobs unless legally required to determine the affected user set — the `user_id` + `entity_type` + `entity_id` on a `chat_messages` row is enough to answer "whose data was accessed" without exposing content.

Write findings into the incident doc as you go. The Comms Lead is reading it live.

## Phase 4 — Notify (the 72-hour track)

**Start this in parallel with Phase 3 the moment personal-data exposure is suspected.** Don't wait for certainty.

| Audience | Trigger | Channel | Deadline |
|----------|---------|---------|----------|
| **Office of the Australian Information Commissioner (OAIC)** | Likely serious harm to Australian individuals (Privacy Act 1988, Notifiable Data Breaches scheme) | https://www.oaic.gov.au/privacy/notifiable-data-breaches | "As soon as practicable" — treat as ≤72 hours from confirmation |
| **EU/UK/EEA supervisory authority** | Personal data of EEA/UK residents was accessed | National DPA portal for each affected jurisdiction | **72 hours** from confirmation (GDPR Art. 33) |
| **Affected users (EEA/UK)** | "High risk to rights and freedoms" — e.g. content leaked, credentials exposed | Email to last-known address; in-app banner if account still active | Without undue delay (GDPR Art. 34); aim for ≤72h alongside DPA filing |
| **Affected users (AU)** | Likely serious harm | Email + in-app banner | "As soon as practicable" |
| **California residents (CCPA/CPRA)** | Statutory PII categories affected | Email + state AG notification if >500 residents | Without unreasonable delay |
| **Stripe** | Suspected card data exposure (should not happen — we only hold Stripe IDs — but verify) | Stripe support; tag as security | Same day |
| **Cyber-insurance carrier** | SEV-1 or SEV-2 | Per policy | Per policy (usually 48-72h) |

**User-facing notification must include:** what happened, what data was involved, what we've done, what the user should do (password reset, monitor accounts, etc.), how to contact us. **Don't** include speculation or apportion blame.

Comms Lead drafts; IC + legal approve before send. Pre-baked templates live in `deployment/incident-comms-templates/` (TODO — write these before the next quarter).

## Phase 5 — Recover

- Restore service from a clean state. If TDE keys or KMS keys were rotated, verify backups still decrypt before declaring recovery (see `BACKUP_RESTORE_RUNBOOK.md`).
- Issue forced password resets where credentials may have been exposed.
- Re-enable any temporarily disabled accounts after verifying they were not compromised.
- Watch SEV-down criteria for 24 hours before closing.

## Phase 6 — Post-mortem (within 7 days of close)

- Blameless write-up in `deployment/postmortems/INC-...md`.
- Identify root cause, contributing factors, dwell time, blast radius.
- File at least one **prevention** action item (not "be more careful") and at least one **detection** action item ("alert when X happens").
- Update this runbook with anything that didn't work.
- Cross-reference into next quarter's security review.

## Pre-flight checklist (do these BEFORE you need them)

- [ ] On-call rotation defined and reachable 24/7
- [ ] Escalation contacts (founder, legal, cyber-insurance) printed somewhere not behind the same auth as production
- [ ] KMS key rotation runbook tested in staging
- [ ] User-notification email template drafted and approved by legal
- [ ] OAIC and EU-DPA reporting forms bookmarked
- [ ] `audit_logs` queries for "actions by user_uuid X in window Y" tested
- [ ] At least one quarterly DR drill (per `BACKUP_RESTORE_RUNBOOK.md`) has passed in the last 3 months

## Escalation contacts

> Maintain in `deployment/contacts.md` — not in this repo's git history.
> The contact list contains personal phone numbers; keep it out of the
> public clone.

The contacts file must include, at minimum:

- IC pager rotation
- Founder / executive on call
- Legal counsel (data protection)
- Cyber-insurance carrier claim line
- AWS support escalation (if Business or Enterprise support)
- Stripe security contact
- OAIC notifiable-breach intake (1300 363 992)
