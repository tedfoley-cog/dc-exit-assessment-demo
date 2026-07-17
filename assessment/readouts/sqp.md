---
app_id: sqp
app_name: Supplier Quality Portal
repo: https://github.com/tedfoley-cog/legacy-supplier-portal
stack: Java 7 / Struts 1.2 / Tomcat 6 / MySQL 5.5
disposition: refactor
blockers: 12
majors: 8
backlog_items: 12
assessed_by: https://app.devin.ai/sessions/d558aa723a3e44af94deb0f7a320f9b2
assessed_date: 2026-07-14
---

# Migration-Readiness Readout — Supplier Quality Portal

## 1. What this application does

The Supplier Quality Portal (SQP) is an internal Struts 1.2 web application used by Supplier Quality Engineering to track supplier quality escapes, corrective action requests (CARs), and first-article inspection (FAI) reports (`README.md:1-7`). Its single data store is the MySQL 5.5 schema `sqp_prod` on `dc1-mysql-prd03`, accessed through raw JDBC connections with no pooling (`src/main/java/com/meridianaero/sqp/util/ConnectionFactory.java:10-28`). Users log in, search and view quality escapes, and upload FAI/inspection reports to the app server's local disk (`src/main/webapp/WEB-INF/struts-config.xml:14-55`). A nightly cron-triggered export writes an open-escape CSV extract to an NFS mount that the ERP nightly batch consumes (`src/main/java/com/meridianaero/sqp/action/NightlyExportAction.java:22-40`; `README.md:26-28`). CAR notification mail is sent to the SQE on-duty distribution list through the DC1 corporate SMTP relay (`src/main/java/com/meridianaero/sqp/util/MailNotifier.java:13-34`).

## 2. Findings by rule

| Rule | Severity | Findings | Evidence |
|---|---|---|---|
| eol-runtime | blocker | 3 findings. Java 7 (Oracle JDK 1.7.0_80, EOL Apr 2015) is the build target and runtime; Tomcat 6.0.53 (EOL Dec 2016) is the app server; MySQL 5.5 (EOL Dec 2018) is the database. | `pom.xml:15-16` (source/target 1.7); `README.md:11-14` |
| vulnerable-dependency | blocker | 5 findings. Struts 1.2.9 (EOL 2008, unfixable CVEs incl. CVE-2014-0114 via beanutils); log4j 1.2.17 (CVE-2019-17571); commons-fileupload 1.2.1 (CVE-2016-1000031 RCE, CVE-2014-0050); commons-beanutils 1.8.0 (CVE-2014-0114); commons-collections 3.2.1 (CVE-2015-6420 deserialization RCE). | `pom.xml:21-25`, `pom.xml:38-42`, `pom.xml:43-47`, `pom.xml:48-52`, `pom.xml:53-57` |
| hardcoded-endpoint | blocker | 3 findings. JDBC URL to `dc1-mysql-prd03.corp.meridianaero.com:3306`; SMTP relay `dc1-smtp-relay01.corp.meridianaero.com:25`; SOAP WSDL on `dc1-wls-app07.corp.meridianaero.com:7001` (Supplier Master, WebLogic 10.3). All are compile-time constants — every one dies when DC1 goes dark. | `src/main/java/com/meridianaero/sqp/util/AppConfig.java:10-11`, `:16-17`, `:27-28` |
| local-filesystem-coupling | major | 3 findings. Nightly export writes to NFS mount `/mnt/dc1-nfs02/erp_inbound/sqp`; uploads stored on local disk `/opt/apps/sqp/uploads` (on the TSM backup schedule); log4j writes to `/opt/apps/sqp/logs/sqp.log`. | `src/main/java/com/meridianaero/sqp/util/AppConfig.java:21`, `:24`; `src/main/java/com/meridianaero/sqp/action/NightlyExportAction.java:39-40`; `src/main/java/com/meridianaero/sqp/action/ReportUploadAction.java:34-45`; `src/main/resources/log4j.properties:4`; `README.md:26-31` |
| plaintext-credentials | blocker | 1 finding. Production DB password for user `sqp_app` committed as a source constant (value redacted here; see evidence). | `src/main/java/com/meridianaero/sqp/util/AppConfig.java:12-13` |
| os-scheduled-job | major | 1 finding. Cron entry on the app server curls `nightlyExport.do` at 02:15 to produce the ERP extract (`15 2 * * * curl -s http://localhost:8080/sqp/nightlyExport.do`). Orchestration lives outside the app and must map to cloud-native scheduling. | `src/main/java/com/meridianaero/sqp/action/NightlyExportAction.java:23-26`; `README.md:26-28` |
| sql-injection | major | 3 findings. Login query concatenates username/password directly into SQL (auth bypass via `' OR '1'='1`); escape search concatenates supplierCode/status; findById concatenates the id. All use `Statement`, no `PreparedStatement` anywhere. | `src/main/java/com/meridianaero/sqp/action/LoginAction.java:29-31`; `src/main/java/com/meridianaero/sqp/dao/EscapeDAO.java:24-33`, `:55-57` |
| missing-test-coverage | major | 1 finding. No test directory, no test framework in `pom.xml`, and the README states regression checks are manual against the QA instance. | absence of `src/test/`; `pom.xml:20-68` (no test deps); `README.md:33-34` |
| shared-database | minor | 1 finding. Integration with ERP is by shared extract file: the ERP nightly batch consumes `SQP_OPEN_YYYYMMDD.csv` from the shared NFS drop zone. No evidence of other apps reading the `sqp_prod` schema directly. | `README.md:26-28`; `src/main/java/com/meridianaero/sqp/action/NightlyExportAction.java:39-47` |

## 3. Environmental coupling inventory

### Hardcoded endpoints

| Endpoint | DC server | Evidence |
|---|---|---|
| `jdbc:mysql://dc1-mysql-prd03.corp.meridianaero.com:3306/sqp_prod` | dc1-mysql-prd03 (DC1, rack B-14 per code comment) | `AppConfig.java:10-11` |
| `dc1-smtp-relay01.corp.meridianaero.com:25` (SMTP) | dc1-smtp-relay01 | `AppConfig.java:16-17` |
| `http://dc1-wls-app07.corp.meridianaero.com:7001/SupplierMaster/SupplierMasterService?WSDL` (SOAP) | dc1-wls-app07 (WebLogic 10.3) | `AppConfig.java:27-28` |
| `http://localhost:8080/sqp/nightlyExport.do` (cron curl target) | dc1-tomcat-app02 | `NightlyExportAction.java:25`; `README.md:14`, `README.md:26-28` |
| Deployment hosts: `dc1-tomcat-app02.corp.meridianaero.com` (prod), `dc1-tomcat-qa01` (QA) | dc1-tomcat-app02 / dc1-tomcat-qa01 | `README.md:14`, `README.md:33-34` |

### File-system dependencies

| Path | Type | Evidence |
|---|---|---|
| `/mnt/dc1-nfs02/erp_inbound/sqp` | NFS mount (dc1-nfs02) — ERP batch drop zone | `AppConfig.java:20-21`; `NightlyExportAction.java:39`; `README.md:26-28` |
| `/opt/apps/sqp/uploads` | Local disk on app server — FAI/inspection report storage, on nightly TSM backup | `AppConfig.java:23-24`; `ReportUploadAction.java:34-45`; `README.md:29-31` |
| `/opt/apps/sqp/logs/sqp.log` | Local disk — daily-rolling log file | `log4j.properties:3-5` |

### Scheduled jobs

| Job | Trigger | Evidence |
|---|---|---|
| Open-escape CSV extract (`SQP_OPEN_YYYYMMDD.csv`) for ERP nightly batch | cron on app server: `15 2 * * * curl -s http://localhost:8080/sqp/nightlyExport.do` (02:15 daily) | `NightlyExportAction.java:23-26`; `README.md:26-28` |
| TSM nightly backup of `/opt/apps/sqp/uploads` | Datacenter TSM backup schedule (outside the app) | `README.md:29-31` |

### Credentials in source

| Credential | Location |
|---|---|
| MySQL user `sqp_app` with plaintext production password (redacted) | `AppConfig.java:12-13` |

Note also: passwords in the `app_user` table are stored as unsalted MD5 (`LoginAction.java:28-31`) — a security finding adjacent to, but distinct from, credentials-in-source.

## 4. Test coverage

There are no automated tests: no `src/test/` directory exists, `pom.xml` declares no test framework (`pom.xml:20-68`), CI only builds the WAR (`.github/workflows/ci.yml:17-18`), and the README confirms regression checks are performed manually against the QA instance (`README.md:33-34`).

A characterization-test baseline needed before remediation can start safely:

- **Login flow**: valid/invalid credential behavior against a seeded `app_user` table, including current MD5 semantics (`LoginAction.java`).
- **Escape search**: result sets for supplier-code/status filter combinations, ordering by `reported_date DESC` (`EscapeDAO.search`).
- **Escape detail**: found/not-found paths (`EscapeDetailAction`, `EscapeDAO.findById`).
- **Report upload**: file persisted under `{UPLOAD_DIR}/{escapeId}/{fileName}`, directory auto-creation, and the notification mail contract (`ReportUploadAction`, `MailNotifier`).
- **Nightly export**: exact CSV header/row format and file naming `SQP_OPEN_YYYYMMDD.csv`, since the ERP batch depends on it byte-for-byte (`NightlyExportAction.java:39-47`).

This requires a disposable MySQL 5.5-compatible fixture database, a fake SMTP sink, and a temp-directory abstraction for the two file paths.

## 5. Remediation backlog

| ID | Item | Rule | Effort | Cloud blocker |
|---|---|---|---|---|
| SQP-01 | Build characterization-test baseline (login, search, detail, upload, export CSV contract) with fixture DB + fake SMTP | missing-test-coverage | M | N |
| SQP-02 | Externalize all configuration in `AppConfig.java` (DB URL, SMTP, WSDL, paths) to environment variables / config service | hardcoded-endpoint | S | Y |
| SQP-03 | Remove DB credentials from source; move to a secrets manager and rotate the `sqp_app` password | plaintext-credentials | S | Y |
| SQP-04 | Replace Struts 1.2.9 web tier (actions/forms/JSP taglibs) with a supported framework (e.g. Spring MVC) — no in-place upgrade path exists | vulnerable-dependency | L | Y |
| SQP-05 | Upgrade runtime: Java 7 → 17/21, Tomcat 6 → 10.x (or embedded server), servlet-api 2.4 → jakarta | eol-runtime | L | Y |
| SQP-06 | Migrate MySQL 5.5 `sqp_prod` schema to a managed cloud database (MySQL 8.x compatible) | eol-runtime | M | Y |
| SQP-07 | Replace log4j 1.2.17 with log4j2/logback and route logs to stdout/log aggregation instead of `/opt/apps/sqp/logs` | vulnerable-dependency | S | Y |
| SQP-08 | Upgrade commons-fileupload, commons-beanutils, commons-collections, javax.mail, mysql-connector to patched versions (bundled with SQP-04/05) | vulnerable-dependency | S | Y |
| SQP-09 | Convert all SQL to `PreparedStatement` with bound parameters (login, search, findById) | sql-injection | S | N |
| SQP-10 | Move report uploads from local disk `/opt/apps/sqp/uploads` to object storage; replaces TSM backup dependency | local-filesystem-coupling | M | Y |
| SQP-11 | Replace NFS drop-zone extract with cloud-native ERP hand-off (object storage bucket or managed transfer) and coordinate the contract change with the ERP batch team | local-filesystem-coupling, shared-database | M | Y |
| SQP-12 | Replace app-server cron with cloud-native scheduler (e.g. EventBridge/Cloud Scheduler) invoking a secured export endpoint or job | os-scheduled-job | S | Y |

## 6. Disposition

**refactor** — SQP cannot be rehosted or trivially replatformed: the entire web tier is Struts 1.2.9, which has been EOL since 2008 with unfixable CVEs, so lifting the WAR into a cloud VM or container carries the vulnerable framework, the EOL Java 7/Tomcat 6 runtime, plaintext production credentials, and SQL injection in the login path into the cloud unchanged. The app is small (5 actions, 1 DAO, ~15 source files) but every layer needs work: 12 blocker findings spanning runtime, dependencies, endpoints, and credentials, plus filesystem and cron coupling that must be redesigned for cloud (object storage, managed scheduler, managed MySQL). Because the app is rated **high criticality** in `portfolio.yaml` (owner: Supplier Quality Engineering) and the ERP nightly batch depends on its extract contract, retire/replace is not on the table without an ERP-side project; a characterization-test-first refactor (SQP-01 first, then SQP-02..12) is the lowest-risk path to the DC1 exit.
