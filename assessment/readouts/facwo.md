---
app_id: facwo
app_name: Facilities Work Order Tracker
repo: https://github.com/tedfoley-cog/legacy-workorder-cf
stack: Adobe ColdFusion 9.0.2 / IIS 7.5 on Windows Server 2008 R2 / Oracle 11g
disposition: replatform
blockers: 10
majors: 9
backlog_items: 12
assessed_by: https://app.devin.ai/sessions/4d952257000c4e598e08bc897dd44131
assessed_date: 2026-07-14
---

# Migration-Readiness Readout — Facilities Work Order Tracker

## 1. What this application does

FACWO is an internal ColdFusion application used by Plant Facilities to track work orders (electrical, HVAC, plumbing, crane/rigging) across the manufacturing campus (`README.md:1-4`). Its primary data store is the `FACWO` schema on Oracle 11g (`dc1-ora-scan02`), accessed through the CF Administrator datasource `facwo_prod` (`README.md:11-13`, `Application.cfc:8-10`). Users create and view work orders through CFML pages (`workorders/create.cfm`, `workorders/detail.cfm`, `index.cfm`); new work orders trigger dispatch e-mails via the `dc1-smtp-relay01` SMTP relay (`components/NotificationService.cfc:9-19`). A nightly CF-Administrator scheduled task pulls the ERP asset master over plain FTP from `dc1-ftp01` and MERGEs it into `asset_master` (`scheduled/erp_asset_sync.cfm:1-43`), and a monthly CSV report is written to the `\\dc1-fs01\facilities\workorder_reports` UNC share for plant management (`reports/export.cfm:13-24`). Consumers are facilities staff, per-craft dispatch queues (`components/WorkOrderService.cfc:56-66`), and plant management via the monthly report.

## 2. Findings by rule

| Rule | Severity | Findings | Evidence |
|---|---|---|---|
| eol-runtime | blocker | 3 findings. (1) Adobe ColdFusion 9.0.2 — core support ended Dec 2014. (2) Windows Server 2008 R2 with IIS 7.5 — extended support ended Jan 2020. (3) Oracle 11g — premier support ended Jan 2015. | `README.md:6-7`, `README.md:11`, `README.md:14`; `README.md:11`; `README.md:12`, `Application.cfc:8-9` |
| vulnerable-dependency | blocker | **No findings.** No third-party libraries, `lib/` directory, or build manifest exist; the app uses only CF9 built-in tags (cfquery/cfmail/cfftp/cffile). Runtime EOL risk is captured under `eol-runtime`. | Full file inventory: 10 CFML files + `README.md` + `.github/workflows/ci.yml` |
| hardcoded-endpoint | blocker | 5 findings. (1) SMTP relay `dc1-smtp-relay01.corp.meridianaero.com`. (2) UNC report share `\\dc1-fs01\facilities\workorder_reports`. (3) FTP host `dc1-ftp01.corp.meridianaero.com`. (4) Absolute app URL `http://dc1-cf9-app01.corp.meridianaero.com/facwo/index.cfm` embedded in dispatch mail. (5) Host name `dc1-cf9-app01` baked into the page footer. | `Application.cfc:13`; `Application.cfc:14`, `reports/export.cfm:23`; `Application.cfc:15`, `scheduled/erp_asset_sync.cfm:8`; `components/NotificationService.cfc:18`; `includes/footer.cfm:8` |
| local-filesystem-coupling | major | 3 findings. (1) FTP drop zone `C:\facwo\inbound\ASSET_MASTER.csv` on local disk of `dc1-cf9-app01`, written then re-read. (2) Monthly CSV written to the `\\dc1-fs01` SMB share. (3) Deployment by robocopy to `D:\inetpub\wwwroot\facwo` — no build artifact. | `scheduled/erp_asset_sync.cfm:16`, `scheduled/erp_asset_sync.cfm:22`; `reports/export.cfm:23-24`; `README.md:18-19` |
| plaintext-credentials | blocker | 2 findings. (1) FTP service account `facwo_svc` / password `Facwo!Ftp2012` committed in source. (2) Application user passwords stored in plain text in `FACWO_USERS` and compared in clear text (hashing ticket FAC-2214 closed "won't fix"). | `scheduled/erp_asset_sync.cfm:9-10`; `login.cfm:2-9` |
| os-scheduled-job | major | 1 finding. "ERP asset sync" registered in the CF Administrator scheduler on `dc1-cf9-app01`, daily 03:30, invoking `http://localhost/facwo/scheduled/erp_asset_sync.cfm`; depends on the ERP 02:00 batch landing the export on `dc1-ftp01`. Scheduler config lives outside the repo. | `README.md:21-25`; `scheduled/erp_asset_sync.cfm:1-4` |
| sql-injection | major | 4 findings. (1) Login query interpolates `form.username` / `form.password` directly. (2) `getWorkOrder` interpolates `url.wo_id` unparameterized. (3) `createWorkOrder` INSERT interpolates all form fields. (4) ERP sync MERGE interpolates raw CSV fields. No `cfqueryparam` anywhere in the codebase. | `login.cfm:5-10`; `components/WorkOrderService.cfc:16-24` (called with `url.wo_id` at `workorders/detail.cfm:4`); `components/WorkOrderService.cfc:40-51`; `scheduled/erp_asset_sync.cfm:28-41` |
| missing-test-coverage | major | 1 finding. No automated tests of any kind: no test directories or frameworks (TestBox/MXUnit) exist, and the README states "There is no build step and no test suite." CI only checks CFML tag balance. | `README.md:19`; `.github/workflows/ci.yml:13-27`; full file inventory |
| shared-database | minor | 1 finding. Integration by extract files rather than DB links: the ERP feeds `asset_master` via a nightly CSV extract on `dc1-ftp01`, and downstream plant-management reporting consumes CSVs from the `\\dc1-fs01` share. No evidence of other apps reading the `FACWO` schema directly. | `README.md:27-31`; `scheduled/erp_asset_sync.cfm:13-18`; `reports/export.cfm:13-24` |

## 3. Environmental coupling inventory

### Hardcoded endpoints
| Endpoint | DC server | Where |
|---|---|---|
| `dc1-smtp-relay01.corp.meridianaero.com:25` (SMTP) | dc1-smtp-relay01 | `Application.cfc:13`, used by `components/NotificationService.cfc:12-13` |
| `\\dc1-fs01\facilities\workorder_reports` (SMB/UNC) | dc1-fs01 | `Application.cfc:14`, `reports/export.cfm:23` |
| `dc1-ftp01.corp.meridianaero.com` (plain FTP) | dc1-ftp01 | `Application.cfc:15`, `scheduled/erp_asset_sync.cfm:8` |
| `http://dc1-cf9-app01.corp.meridianaero.com/facwo/` (app URL in outbound mail) | dc1-cf9-app01 | `components/NotificationService.cfc:18`, `README.md:14` |
| `dc1-ora-scan02` (Oracle 11g, via CF Administrator datasource `facwo_prod`) | dc1-ora-scan02 | `README.md:12-13`, `Application.cfc:8-10` |

### File-system dependencies
- `C:\facwo\inbound\ASSET_MASTER.csv` — local-disk FTP drop zone on `dc1-cf9-app01` (`scheduled/erp_asset_sync.cfm:16,22`)
- `\\dc1-fs01\facilities\workorder_reports\WO_MONTHLY_YYYYMM.csv` — monthly report written to SMB share (`reports/export.cfm:23-24`)
- `D:\inetpub\wwwroot\facwo` — deployment target, robocopy from a release share (`README.md:18-19`)
- `facwo_sync` CF log file on the app server (`scheduled/erp_asset_sync.cfm:45`)

### Scheduled jobs
| Job | Trigger | Template | Coupling |
|---|---|---|---|
| ERP asset sync | CF Administrator scheduler, daily 03:30 | `scheduled/erp_asset_sync.cfm` | Scheduler config lives on `dc1-cf9-app01` outside source control; implicit dependency on the ERP 02:00 batch landing `/exports/ASSET_MASTER.csv` on `dc1-ftp01` (`scheduled/erp_asset_sync.cfm:1-4`, `README.md:21-25`) |

### Credentials in source
- FTP service account `facwo_svc`, password `Facwo!Ftp2012` (`scheduled/erp_asset_sync.cfm:9-10`)
- Application user passwords stored and compared in plain text in the `FACWO_USERS` table (`login.cfm:2-9`)
- Oracle credentials live in the CF Administrator datasource `facwo_prod` (not in source, but unmanaged server-local config — `Application.cfc:8-10`)

## 4. Test coverage

None. There is no test suite, no build step (`README.md:19`), and no test framework anywhere in the repo; the only CI is a tag-balance sanity check (`.github/workflows/ci.yml:13-27`). Before remediation can start safely, a characterization-test baseline needs to cover: (1) login/session gating (`Application.cfc:20-27`, `login.cfm`); (2) open-work-order listing (`WorkOrderService.getOpenWorkOrders`); (3) work-order creation including WO-number formatting and dispatch-queue routing per craft (`WorkOrderService.createWorkOrder`, `assignmentQueueForCraft`); (4) work-order detail retrieval; (5) monthly CSV content and naming (`reports/export.cfm`); and (6) the ERP CSV MERGE semantics, including the header-skip and 4-field minimum (`scheduled/erp_asset_sync.cfm:24-43`). This requires a disposable CF (or Lucee) runtime plus a seeded Oracle-compatible schema, with SMTP/FTP/file-share faked at the boundary.

## 5. Remediation backlog

| ID | Item | Rule | Effort | Cloud blocker |
|---|---|---|---|---|
| FACWO-01 | Stand up characterization-test baseline (Lucee/CF container + seeded DB, boundary fakes for SMTP/FTP/share) covering the six behaviors in §4 | missing-test-coverage | M | N |
| FACWO-02 | Migrate runtime off ColdFusion 9 to a supported engine (Lucee 6 / ACF 2023) in a Linux container; remove IIS/Windows 2008 R2 dependency | eol-runtime | L | Y |
| FACWO-03 | Migrate database off Oracle 11g to a supported managed target (Oracle 19c+ managed service or PostgreSQL); port `facwo_seq`, `SYSDATE`, `ADD_MONTHS`, `MERGE` usages | eol-runtime | L | Y |
| FACWO-04 | Externalize all endpoints (`smtpServer`, `reportShare`, `erpFtpHost`, datasource, app base URL) from `Application.cfc:13-15` / `NotificationService.cfc:18` into environment-based configuration | hardcoded-endpoint | S | Y |
| FACWO-05 | Remove FTP credentials from `scheduled/erp_asset_sync.cfm:9-10`; rotate `facwo_svc` and source secrets from a vault/secret manager | plaintext-credentials | S | Y |
| FACWO-06 | Hash application user passwords and rework login verification (`login.cfm:2-14`); one-time migration of `FACWO_USERS` | plaintext-credentials | M | Y |
| FACWO-07 | Replace plain-FTP asset intake and the `C:\facwo\inbound` drop zone with object storage (e.g. S3/Blob) or SFTP-to-object-store ingestion | hardcoded-endpoint, local-filesystem-coupling | M | Y |
| FACWO-08 | Replace `\\dc1-fs01` UNC report write with object storage or e-mail delivery; update plant-management pickup process | local-filesystem-coupling | S | Y |
| FACWO-09 | Re-home the "ERP asset sync" CF Administrator scheduled task to cloud-native scheduling (e.g. EventBridge/Cloud Scheduler → app endpoint or job); capture schedule as code | os-scheduled-job | S | Y |
| FACWO-10 | Parameterize all SQL with `cfqueryparam` (login, getWorkOrder, createWorkOrder, ERP MERGE) | sql-injection | S | N |
| FACWO-11 | Point outbound mail at a cloud SMTP/API relay and fix the hardcoded review URL in dispatch notifications | hardcoded-endpoint | S | Y |
| FACWO-12 | Replace robocopy deployment with a pipeline-built container image; capture datasource and scheduler config as code | eol-runtime, os-scheduled-job | M | N |

## 6. Disposition

**replatform** — FACWO is a small (10 CFML files), well-understood, medium-criticality departmental app whose business logic is sound but whose entire runtime stack (CF9, Windows 2008 R2/IIS 7.5, Oracle 11g) is past end of support, ruling out a straight rehost. The backlog is dominated by environmental decoupling (5 hardcoded endpoints, 3 filesystem couplings, 1 external scheduler) plus credential and SQL-parameterization hygiene — all mechanical changes that do not require re-architecting the application. Replatforming onto a supported CFML engine (Lucee/ACF 2023) in a container with a managed database, externalized configuration, object storage in place of FTP/UNC shares, and cloud-native scheduling retires all 10 blockers with roughly 12 backlog items (2 L, 4 M, 6 S). A full refactor/rewrite is not justified by the app's medium criticality, and retire/replace is not indicated because Plant Facilities depends on it daily with no successor system identified.
