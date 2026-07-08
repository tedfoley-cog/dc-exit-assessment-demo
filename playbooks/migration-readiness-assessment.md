# Playbook: Migration-Readiness Assessment (per application)

You are assessing one legacy application for cloud migration readiness as
part of a data-center exit. You have **read-only** access to the repo. Do
not modify the application repository. Your deliverable is a readout file
committed to the `dc-exit-assessment-demo` repo.

## Inputs

- `APP_REPO`: the application repository URL (from `portfolio.yaml`)
- `APP_ID`: the app id (from `portfolio.yaml`)
- Ruleset: `rules/cloud-readiness-rules.yaml` in this repo
- Readout structure: `assessment/READOUT_TEMPLATE.md`

## Steps

1. **Index the repository.** Clone `APP_REPO` and read every source file.
   Confirm the repo is indexed in DeepWiki (https://deepwiki.com) so the
   audience can browse the generated architecture wiki; trigger indexing
   if it is not.

2. **Establish what the app does.** Write a 3–5 sentence behavioral
   summary: business purpose, primary data stores, integrations, batch
   jobs, and who depends on it. Ground every claim in a file you read.

3. **Apply the readiness ruleset.** For every rule in
   `rules/cloud-readiness-rules.yaml`, search the codebase for violations.
   Every finding must cite `file:line` (or file + section for non-line
   formats like JCL). No finding without evidence; no rule skipped —
   record "no findings" explicitly where clean.

4. **Inventory environmental coupling.** Produce the concrete lists:
   - hardcoded hostnames / endpoints (with the DC server each points at)
   - file-system paths and mounts (local disk, NFS, UNC shares)
   - scheduled jobs and their triggers (cron, CF scheduler, CA-7)
   - credentials found in source

5. **Assess test coverage.** State what automated tests exist (typically
   none) and what a characterization-test baseline would need to cover
   before remediation can start safely.

6. **Build the remediation backlog.** One table row per work item:
   `ID | Item | Rule | Effort (S/M/L) | Blocker for cloud? (Y/N)`.
   Items must be concrete enough to hand to an engineer (or a Devin
   session) as a work order.

7. **Assign a disposition.** One of `rehost / replatform / refactor /
   retire / replace`, with a short justification paragraph that weighs
   the backlog size against the app's criticality in `portfolio.yaml`.

8. **Write the readout.** Fill in `assessment/READOUT_TEMPLATE.md` and
   commit it as `assessment/readouts/<APP_ID>.md` on a branch of the
   `dc-exit-assessment-demo` repo; open a PR.

## Rules of engagement

- Read-only on the application repo. All output goes to the assessment repo.
- Every finding cites evidence. If you cannot find evidence, it is not a
  finding.
- Do not fix anything. The backlog is the deliverable, not the remediation.
