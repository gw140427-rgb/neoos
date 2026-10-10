# NeoOS 7-day development plan

Date: 2026-10-10
Repository: gw140427-rgb/neoos
Baseline: main at 0b8add858cbad6b327e318407c68ca579e7197e1
Status: Day 1 research and planning only; no feature implementation in this session.

## Findings
- Neoos.py is the Python educational shell simulator.
- test_neoos.py contains 45 unit tests; the documented command is python3 -m unittest test_neoos -v.
- compose.yaml, linux/Dockerfile, and linux/bridge.py define the current Podroid Alpine -> Docker -> Debian Bookworm path.
- The Compose service uses a read-only root filesystem, dropped capabilities, no-new-privileges, and resource limits.
- os/build.sh uses an x86_64 package list, so ARM64 compatibility must not be assumed.
- No AGENTS.md or separate agent instruction file was found on main.
- Branch docs/neoos-ai-autodev-plan is two documentation commits ahead of main and contains a prior design/specification. It is not merged.
- PR #5 (codex/linux-container-ci) is open. Do not modify its branch.

## Existing validation evidence
- GitHub Actions run Tests #37911502421 succeeded on 2026-10-09; Python 3.10 and 3.12 test and CLI smoke-test jobs succeeded.
- NeoOS CI run #37911502424 succeeded.
- Docker Image CI run #37911502433 failed because the root Dockerfile refers to server.py, which is absent from main. This was confirmed in the remote job log; no local Docker build was performed here.
- Actual A16/Podroid resource state and ARM64 device behavior were not checked in this remote inspection.

## Prioritized 7-day sequence
Day 1 — Inspect architecture, instructions, tests, CI, branches and open PRs; write this plan.
Day 2 — Add a small read-only repository diagnostics/safety capability. Refuse mutation when repository state is unclear.
Day 3 — Add tests for clean/dirty worktrees, detached HEAD, missing Git, invalid paths, and failure/timeout reporting.
Day 4 — Check ARM64, Termux and Debian assumptions only where repository files or available CI provide evidence. Do not claim device validation without a device run.
Day 5 — Document setup, expected output, recovery, and known limits without changing the current Podroid/Docker/Debian usage.
Day 6 — Run available tests and review all diffs. Investigate the existing root Dockerfile CI failure and PR #5; only fix a reproducible, understood issue on a separate branch.
Day 7 — Audit changes, branches, PRs, test evidence, safety policy and unresolved issues; report results without auto-merging.

## Safety and cost rules
- Work on a dedicated non-main branch and use a draft PR for review.
- Preserve existing user changes, branches, containers, volumes, and data.
- No paid API, card registration, new cloud spending, automatic deployment, or automatic merge.
- Report the exact tests and evidence. Skipped or unexecuted tests are not passes.
- Each scheduled run is bounded; continuous seven-day execution is not guaranteed.
