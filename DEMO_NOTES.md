# Demo Cheat Sheet — Migration-Readiness Assessment

## Setup (do this before joining the call)
- [ ] Open tabs: this repo, the three `legacy-*` tranche repos, and deepwiki.com (search box ready)
- [ ] Confirm org session concurrency allows 4 simultaneous sessions

## Demo Flow
1. Frame it: "nobody fully knows what 2,000 apps do — this is the assessment SIs spend months on; watch it happen on a real tranche, read-only, in one hour."
2. In a fresh Devin session, prompt: "Run the migration-readiness assessment in `playbooks/migration-readiness-assessment.md` over every app in `portfolio.yaml`, one child session per app, then aggregate the readouts."
3. While sessions run, walk the tranche repos: Struts 1.2 with hardcoded DC hostnames, ColdFusion with plaintext FTP creds, COBOL/JCL with CA-7 coupling — "this is what the estate really looks like."
4. Show DeepWiki pages materializing per repo — the "ask the codebase" interface planners keep for the whole program.
5. Open the readout PRs as they land: every finding has file:line evidence; point at the disposition and the sized backlog.
6. Close on the aggregated portfolio table: "these backlogs are the factory's work queue — the paid next step — and every artifact belongs to you, not an SI."
