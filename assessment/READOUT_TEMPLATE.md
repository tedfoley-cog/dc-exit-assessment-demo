---
app_id: <id from portfolio.yaml>
app_name: <name>
repo: <url>
stack: <stack summary>
disposition: <rehost|replatform|refactor|retire|replace>
blockers: <count of blocker-severity findings>
majors: <count of major-severity findings>
backlog_items: <count>
assessed_by: <devin session url>
assessed_date: <YYYY-MM-DD>
---

# Migration-Readiness Readout — <App Name>

## 1. What this application does

<3–5 sentences, evidence-grounded.>

## 2. Findings by rule

| Rule | Severity | Findings | Evidence |
|---|---|---|---|
| eol-runtime | blocker | ... | `file:line` |
| vulnerable-dependency | blocker | ... | `file:line` |
| hardcoded-endpoint | blocker | ... | `file:line` |
| local-filesystem-coupling | major | ... | `file:line` |
| plaintext-credentials | blocker | ... | `file:line` |
| os-scheduled-job | major | ... | `file:line` |
| sql-injection | major | ... | `file:line` |
| missing-test-coverage | major | ... | ... |
| shared-database | minor | ... | ... |

## 3. Environmental coupling inventory

### Hardcoded endpoints
### File-system dependencies
### Scheduled jobs
### Credentials in source

## 4. Test coverage

<Current state and required characterization-test baseline.>

## 5. Remediation backlog

| ID | Item | Rule | Effort | Cloud blocker |
|---|---|---|---|---|
| <APP>-01 | ... | ... | S/M/L | Y/N |

## 6. Disposition

**<disposition>** — <justification>
