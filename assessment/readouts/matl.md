---
app_id: matl
app_name: Materials Inventory Batch
repo: https://github.com/tedfoley-cog/legacy-inventory-cobol
stack: Enterprise COBOL 4.2 / z/OS 2.3 / VSAM / CA-7
disposition: refactor
blockers: 3
majors: 3
backlog_items: 8
assessed_by: https://app.devin.ai/sessions/c01bb68aabc8496588a2d83a22e4790a
assessed_date: 2026-07-14
---

# Migration-Readiness Readout — Materials Inventory Batch

## 1. What this application does

MATL is a mainframe batch suite (original development 1998) that maintains the plant materials inventory master for Meridian Aerostructures' Materials Management group (`README.md:1-8`, `src/INVRPT.cbl` header constant `MERIDIAN AEROSTRUCTURES - MATERIALS`). Nightly, the CA-7-scheduled job `INVDAILY` sorts the day's storeroom transactions and `INVMAIN` posts receipts/issues/adjustments against the VSAM KSDS master `MATL.INV.MASTER.VSAM`, writing failed transactions to a rejects GDG that the materials control desk reworks each morning (`jcl/INVDAILY.jcl`, `src/INVMAIN.cbl` header, `README.md:31-33`). Field validation is delegated to the called subprogram `INVEDIT` (tran type, part number, quantity, hazmat class table, date — `src/INVEDIT.cbl:9-15`). `INVRPT` prints a reorder-point exception report to SYSOUT that materials planners pick up from the spool (`src/INVRPT.cbl:6-9`). Weekly, `INVWKLY` flattens the master with IDCAMS REPRO and pushes the valuation extract by plain FTP to `dc1-ftp01` where the ERP integration consumes it (`jcl/INVWKLY.jcl`, `README.md:33-34`) — the downstream ERP nightly batch at 05:00 depends on INVDAILY completing first (`README.md:31-32`).

## 2. Findings by rule

| Rule | Severity | Findings | Evidence |
|---|---|---|---|
| eol-runtime | blocker | Enterprise COBOL for z/OS 4.2 (EOS 2022) on z/OS 2.3 (EOS 2022); both past end of support | `README.md:7-8` |
| vulnerable-dependency | blocker | **No findings.** No third-party libraries; only IBM system utilities (SORT, IDCAMS, FTP) and in-repo copybooks | `jcl/INVDAILY.jcl` STEP010, `jcl/INVWKLY.jcl` STEP010/020 |
| hardcoded-endpoint | blocker | FTP target `dc1-ftp01.corp.meridianaero.com` hardcoded in the weekly extract job's FTP input stream; also referenced operationally in the README | `jcl/INVWKLY.jcl` STEP020 `//INPUT DD *` (line 21); `README.md:33-34` |
| local-filesystem-coupling | major | Hardcoded dataset DSNs throughout JCL: `MATL.INV.TRANS.DAILY`, `MATL.INV.MASTER.VSAM`, `MATL.INV.REJECTS(+1)` GDG, `MATL.PROD.LOADLIB`, `MATL.INV.EXTRACT.WEEKLY`; remote drop-zone path `/exports/INV_VALUATION.dat` on dc1-ftp01; report output to JES SYSOUT spool | `jcl/INVDAILY.jcl` lines 12, 20, 22, 23, 28; `jcl/INVWKLY.jcl` lines 10, 11, 24; `src/INVRPT.cbl:19-20` (RPTOUT → `//RPTOUT DD SYSOUT=A`, `jcl/INVDAILY.jcl` line 30) |
| plaintext-credentials | blocker | FTP service-account userid `matlbtch` and password `M@tl2009` committed in the JCL FTP input stream | `jcl/INVWKLY.jcl` STEP020 `//INPUT DD *` (lines 22-23) |
| os-scheduled-job | major | Batch orchestration lives in CA-7 outside the app: INVDAILY runs after the 23:00 storeroom cutoff with a hard dependency of finishing before the 05:00 ERP batch; INVWKLY runs weekly | `README.md:8,31-32`; `jcl/INVDAILY.jcl` comment "SCHEDULED VIA CA-7" (line 5); `src/INVMAIN.cbl` header comment (lines 11-12) |
| sql-injection | major | **No findings.** No SQL anywhere; all data access is VSAM/sequential file I/O | `src/INVMAIN.cbl` FILE-CONTROL (lines 22-32); `src/INVRPT.cbl:14-20` |
| missing-test-coverage | major | No automated test suite; changes verified manually by running jobs against a master copy in the TEST LPAR | `README.md:35-36`; no test directories or frameworks in repo |
| shared-database | minor | Master data shared with the ERP by weekly flat-file extract (`MATL.INV.EXTRACT.WEEKLY` → `/exports/INV_VALUATION.dat`); transactions produced by the separate storeroom 3270 data-entry application | `jcl/INVWKLY.jcl` STEP010/020; `README.md:4-5,26-28,33-34`; `copybooks/INVTRAN.cpy:3` |

## 3. Environmental coupling inventory

### Hardcoded endpoints
- `dc1-ftp01.corp.meridianaero.com` — DC1 ERP landing/FTP server; weekly valuation extract pushed by plain FTP (`jcl/INVWKLY.jcl` STEP020 line 21; `README.md:33-34`)

### File-system dependencies
- `MATL.INV.MASTER.VSAM` — inventory master VSAM KSDS, key = part number (`jcl/INVDAILY.jcl` line 22; `jcl/INVWKLY.jcl` line 10; `README.md:25`)
- `MATL.INV.TRANS.DAILY` — daily storeroom transaction file (`jcl/INVDAILY.jcl` line 12)
- `MATL.INV.REJECTS(+1)` — GDG of rejected transactions for morning rework (`jcl/INVDAILY.jcl` line 23)
- `MATL.INV.EXTRACT.WEEKLY` — weekly valuation flat file (`jcl/INVWKLY.jcl` line 11)
- `MATL.PROD.LOADLIB` — production load library (STEPLIB, `jcl/INVDAILY.jcl` lines 20, 28)
- `/exports/INV_VALUATION.dat` — drop zone on dc1-ftp01 consumed by the ERP integration (`jcl/INVWKLY.jcl` line 24)
- JES SYSOUT spool — INVRPT report picked up by planners from the spool (`jcl/INVDAILY.jcl` line 30; `src/INVRPT.cbl:8-9`)

### Scheduled jobs
- `INVDAILY` — nightly via CA-7 after the 23:00 storeroom cutoff; must complete before the 05:00 ERP nightly batch (`jcl/INVDAILY.jcl` line 5; `README.md:31-32`)
- `INVWKLY` — weekly via CA-7; valuation extract + FTP to ERP (`jcl/INVWKLY.jcl`; `README.md:18`)

### Credentials in source
- FTP service account `matlbtch` / password `M@tl2009` in cleartext (`jcl/INVWKLY.jcl` STEP020 lines 22-23)

## 4. Test coverage

There is no automated test suite; the README states changes are verified by running the jobs against a copy of the master in the TEST LPAR (`README.md:35-36`). Before remediation can start safely, a characterization-test baseline must cover: (1) INVMAIN posting semantics for R/I/A transaction types including the A-type overwrite behavior (`src/INVMAIN.cbl` 4100-POST-QUANTITY), rejects for parts not on master, and reject-record layout; (2) all INVEDIT edit rules — tran type, blank part number, non-numeric/zero quantity, the 6-entry hazmat class table, and date range checks (`src/INVEDIT.cbl`); (3) INVRPT selection logic (on-hand + on-order < reorder point) and report formatting (`src/INVRPT.cbl` 2000-CHECK-PART); (4) the weekly extract record layout consumed by the ERP (200-byte `copybooks/INVMAST.cpy` image). The repo's `data/sample_transactions.dat` (which includes deliberate bad records, e.g. tran type `X`) is a usable seed for golden-file tests.

## 5. Remediation backlog

| ID | Item | Rule | Effort | Cloud blocker |
|---|---|---|---|---|
| MATL-01 | Build characterization-test baseline: golden-file tests for INVMAIN/INVEDIT/INVRPT using `data/sample_transactions.dat` plus a seeded master, covering posting, edits, rejects, and report output | missing-test-coverage | M | N |
| MATL-02 | Migrate off Enterprise COBOL 4.2 / z/OS 2.3: recompile or transpile INVMAIN/INVEDIT/INVRPT to a supported runtime (COBOL 6.x on an emulation platform, or a managed batch runtime) | eol-runtime | L | Y |
| MATL-03 | Replace hardcoded FTP push to `dc1-ftp01.corp.meridianaero.com` with a managed, configurable transfer (e.g. SFTP/object storage) — endpoint externalized from JCL | hardcoded-endpoint | S | Y |
| MATL-04 | Remove `matlbtch`/`M@tl2009` credentials from `INVWKLY.jcl`; rotate the account and source credentials from a secrets manager | plaintext-credentials | S | Y |
| MATL-05 | Migrate VSAM master and dataset dependencies (`MATL.INV.*` DSNs, rejects GDG, load library) to cloud-equivalent storage (indexed datastore / object storage with retention for the GDG) | local-filesystem-coupling | L | Y |
| MATL-06 | Re-map CA-7 schedules and dependencies (23:00 cutoff trigger, 05:00 ERP predecessor constraint, weekly cycle) to a cloud-native scheduler/orchestrator | os-scheduled-job | M | Y |
| MATL-07 | Replace the weekly flat-file extract integration to the ERP with a supported interface (API or managed file transfer with a defined contract), coordinating cutover with the ERP team | shared-database | M | N |
| MATL-08 | Replace SYSOUT-spool delivery of the reorder exception report with a distributable output (file/email/dashboard) for the materials planners | local-filesystem-coupling | S | N |

## 6. Disposition

**refactor** — MATL is high-criticality (nightly feed gating the 05:00 ERP batch) but very small: three COBOL programs (~600 lines total), two copybooks, and two JCL members with plain, well-understood batch logic (sort → post → report; extract → FTP). A pure rehost is not available because every layer is mainframe-bound — Enterprise COBOL 4.2/z/OS 2.3 (EOL runtime), VSAM KSDS storage, CA-7 orchestration, JES spool output, and a plaintext-credential FTP push — so the 3 blockers and 3 majors above must be addressed regardless of target. Given the tiny footprint, a refactor to a supported runtime with cloud-native storage, scheduling, and transfer (backlog MATL-02..MATL-06) is lower total cost and risk than licensing a mainframe-emulation replatform for a 5-file suite, and the characterization baseline (MATL-01) is cheap to build from the included sample data. Retire/replace is not on the table: Materials Management depends on it daily and the ERP consumes its extract weekly.
