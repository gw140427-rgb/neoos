# NeoOS AI Auto-Development Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dependency-free, local-first execution core that safely checks the NeoOS workspace, runs explicitly allowed tests, records resumable checkpoints, and stops within bounded retry/time limits.

**Architecture:** Add a separate `neoos_autodev` Python package without changing the existing NeoOS simulator, installer, or Docker runtime. The first milestone provides a policy-enforced task runner, workspace guard, state/report storage, and CLI; AI-generated patches and cloud deployment integrations remain separate later plans.

**Tech Stack:** Python standard library only; `unittest`; Git CLI invoked only for read-only status/branch checks in the first milestone.

**Spec:** `docs/superpowers/specs/2026-10-09-neoos-ai-auto-development-design.md`

## Global Constraints

- Target Android ARM64 Podroid/Alpine; optionally run existing tests in the established Debian container, without recreating or deleting existing containers/volumes.
- Preserve user changes; refuse mutation when the workspace has uncommitted changes or the branch/state is unexpected.
- Never write directly to `main`; do not run `git reset --hard`, `git clean -fd`, force-push, arbitrary shell commands, or deletion operations.
- Use Python standard library only in milestone 1; no paid API, API key, network access, or cloud dependency is required.
- Default run deadline is at most 24 hours; each test command has a shorter timeout; automated repair attempts are capped at 3 per task.
- A test that was skipped, timed out, or could not run must never be reported as passing.
- Do not merge, push, or deploy automatically; require explicit human approval for those operations.
- Never store tokens, API keys, cookies, private keys, or complete environment variables in state files or logs.

## Review Focus

- Dirty or detached Git workspace: guard must stop before any file mutation; test in Task 2.
- Malformed, truncated, or incompatible checkpoint: report invalid state and require review rather than silently resetting; test in Task 1.
- Test process timeout or child-process failure: terminate safely, record timeout/nonzero exit, and do not count it as success; test in Task 3.
- Deadline already expired or shorter than the next step: do not start another task or retry; test in Task 4.
- Paths containing spaces, symlinks, or traversal components: reject paths outside the repository and avoid following links outside the allowed root; test in Task 2.

---

## File Structure

- Create `neoos_autodev/__init__.py`: package version and public exports.
- Create `neoos_autodev/models.py`: task, run, command result, and status data structures.
- Create `neoos_autodev/state.py`: atomic JSON checkpoint read/write and redacted run report output.
- Create `neoos_autodev/workspace.py`: read-only Git/worktree and allowed-path checks.
- Create `neoos_autodev/runner.py`: fixed command allowlist, per-command timeout, deadline and retry policy.
- Create `neoos_autodev/cli.py`: `check` and `run-tests` commands with safe defaults.
- Create `tests_autodev/__init__.py` and focused `unittest` modules for each component.
- Modify `.github/workflows/ci.yml`: run the new core tests alongside existing NeoOS tests, retaining current Python matrix and timeout.
- Modify `README.md`: document the optional local core CLI and its limitations; do not change current Docker usage instructions.

## Interfaces

- `models.TaskSpec(task_id: str, goal: str, allowed_paths: tuple[str, ...], test_commands: tuple[str, ...])`
- `models.CommandResult(command: tuple[str, ...], returncode: int | None, stdout: str, stderr: str, timed_out: bool, duration_seconds: float)`
- `models.RunState(run_id: str, started_at: str, deadline_at: str, status: str, current_task_id: str | None, repair_attempts: int, last_checkpoint: str | None)`
- `state.save_state(path: Path, state: RunState) -> None`
- `state.load_state(path: Path) -> RunState` raises a typed validation error for invalid/incompatible state.
- `workspace.inspect_workspace(repo: Path) -> WorkspaceSnapshot` returns current branch, clean/dirty status, and HEAD SHA without modifying files.
- `workspace.validate_allowed_paths(repo: Path, paths: tuple[str, ...]) -> None` raises `WorkspaceSafetyError` for traversal, absolute paths, or symlink escape.
- `runner.run_allowed_command(command_id: str, repo: Path, timeout_seconds: float, deadline_at: datetime) -> CommandResult` runs only a built-in command ID, never a caller-supplied arbitrary shell string.
- `runner.can_start_step(now: datetime, deadline_at: datetime) -> bool`
- `cli.main(argv: list[str] | None = None) -> int`

## Task 1: Define State Models and Durable Checkpoints

**Files:**
- Create: `neoos_autodev/__init__.py`
- Create: `neoos_autodev/models.py`
- Create: `neoos_autodev/state.py`
- Create: `tests_autodev/__init__.py`
- Create: `tests_autodev/test_state.py`

- [ ] **Step 1: Write failing model and state tests**
  - Test round-trip serialization of `RunState`.
  - Test that missing required fields, wrong field types, unknown status values, and invalid timestamps raise a typed validation error.
  - Test that a save uses a temporary sibling file and atomic replacement, leaving no temporary file on success.
  - Test that report serialization omits environment variables and secret-like values.
- [ ] **Step 2: Run tests and confirm the expected failures**
  - Run: `python3 -m unittest tests_autodev.test_state -v`
  - Expected: FAIL because the package/models/state module is not implemented.
- [ ] **Step 3: Implement models and atomic state storage**
  - Use dataclasses and JSON from the standard library.
  - Validate required fields and allow only the documented statuses: `pending`, `running`, `passed`, `failed`, `stopped`, `needs_review`.
  - Write to a temporary file in the same directory, flush and fsync, then replace atomically.
  - Never serialize full process environments, credentials, or arbitrary exception object representations.
- [ ] **Step 4: Run state tests**
  - Run: `python3 -m unittest tests_autodev.test_state -v`
  - Expected: PASS, with malformed checkpoint tests proving safe rejection.
- [ ] **Step 5: Commit the isolated component**
  - Commit message: `feat: add validated autodev checkpoint state`

## Task 2: Add Read-Only Workspace Safety Guards

**Files:**
- Create: `neoos_autodev/workspace.py`
- Create: `tests_autodev/test_workspace.py`

- [ ] **Step 1: Write failing workspace tests**
  - Test clean branch/HEAD detection using a temporary Git repository.
  - Test dirty workspace detection without changing the tracked or untracked files.
  - Test that `main`, detached HEAD, missing Git, and unexpected repository root produce a refusal result for mutation-ready mode.
  - Test rejection of absolute paths, `..` traversal, and symlinks resolving outside the repository; test that valid nested paths and paths containing spaces are accepted.
- [ ] **Step 2: Run tests and confirm expected failures**
  - Run: `python3 -m unittest tests_autodev.test_workspace -v`
  - Expected: FAIL until workspace inspection and path validation exist.
- [ ] **Step 3: Implement read-only workspace inspection**
  - Use `subprocess.run` with argument arrays, `shell=False`, bounded timeouts, and no write-capable Git commands.
  - Return a snapshot with HEAD SHA, branch/detached state, and dirty status.
  - Refuse mutation-ready execution on `main`, detached HEAD, dirty workspace, or unknown Git state.
  - Resolve paths under the repository root and reject traversal or symlink escape.
- [ ] **Step 4: Run workspace tests**
  - Run: `python3 -m unittest tests_autodev.test_workspace -v`
  - Expected: PASS; all safety checks leave test fixture files unchanged.
- [ ] **Step 5: Commit**
  - Commit message: `feat: guard autodev workspace state`

## Task 3: Implement the Allowlisted Test Runner

**Files:**
- Create: `neoos_autodev/runner.py`
- Create: `tests_autodev/test_runner.py`

- [ ] **Step 1: Write failing runner tests**
  - Test built-in command IDs for Python syntax checking and the existing unit-test suite.
  - Test unknown command IDs are rejected without spawning a process.
  - Test nonzero exit codes remain failures and stdout/stderr are captured.
  - Test timeout sets `timed_out=True`, terminates the child process, and cannot be reported as passed.
  - Test a deadline earlier than the current time prevents process launch.
- [ ] **Step 2: Run tests and confirm expected failures**
  - Run: `python3 -m unittest tests_autodev.test_runner -v`
  - Expected: FAIL until the allowlisted runner exists.
- [ ] **Step 3: Implement the runner**
  - Use a fixed mapping of command IDs to argument arrays; initial IDs: `python-syntax` and `neoos-unit-tests`.
  - `neoos-unit-tests` maps to `python3 -m unittest test_neoos -v`; syntax check is limited to explicitly selected Python files inside the repository.
  - Never accept raw shell text from an AI/model or CLI argument.
  - Apply a conservative per-command timeout and the overall deadline; record exit status, duration, and timeout separately.
- [ ] **Step 4: Run runner tests**
  - Run: `python3 -m unittest tests_autodev.test_runner -v`
  - Expected: PASS, including timeout and disallowed-command tests.
- [ ] **Step 5: Commit**
  - Commit message: `feat: add allowlisted autodev test runner`

## Task 4: Add Bounded Run Control and Retry Accounting

**Files:**
- Modify: `neoos_autodev/models.py`
- Create: `neoos_autodev/controller.py`
- Create: `tests_autodev/test_controller.py`

- [ ] **Step 1: Write failing controller tests**
  - Test a run deadline is capped at 24 hours even if a larger duration is requested.
  - Test expired deadlines prevent starting another task or retry.
  - Test a task allows at most 3 repair attempts and the next failure becomes `needs_review`.
  - Test repeated identical failure signatures stop early.
  - Test restart state that conflicts with the current Git HEAD becomes `needs_review`, not automatic resume.
- [ ] **Step 2: Run tests and confirm expected failures**
  - Run: `python3 -m unittest tests_autodev.test_controller -v`
  - Expected: FAIL until run control exists.
- [ ] **Step 3: Implement deterministic run control**
  - Add `controller.create_run_state(now: datetime, requested_hours: float) -> RunState`, `controller.can_start_step(now, state) -> bool`, and `controller.record_repair_attempt(state, failure_signature: str) -> RunState`.
  - Clamp requested duration to a positive value no greater than 24 hours.
  - Stop starting work when the deadline is reached, after 3 repair attempts, or on a repeated failure signature.
  - Keep restart reconciliation read-only; if saved HEAD/branch and current workspace differ, require review.
- [ ] **Step 4: Run controller tests**
  - Run: `python3 -m unittest tests_autodev.test_controller -v`
  - Expected: PASS; boundary tests cover the 24-hour maximum and 3-attempt maximum.
- [ ] **Step 5: Commit**
  - Commit message: `feat: enforce autodev time and retry limits`

## Task 5: Add CLI, End-to-End Tests, and Documentation

**Files:**
- Create: `neoos_autodev/cli.py`
- Create: `tests_autodev/test_cli.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`

- [ ] **Step 1: Write failing CLI and integration tests**
  - Test `check` reports branch, HEAD, and dirty status without writing to the workspace.
  - Test `run-tests` refuses `main`, dirty workspaces, and unknown command IDs before running a test.
  - Test a passing allowed test creates a report with actual exit status and a passing state.
  - Test a failing/timeout test creates a failure report and never claims success.
  - Test the CLI returns nonzero on refusal or failed tests.
- [ ] **Step 2: Run tests and confirm expected failures**
  - Run: `python3 -m unittest tests_autodev.test_cli -v`
  - Expected: FAIL until CLI integration exists.
- [ ] **Step 3: Implement CLI**
  - Expose `python3 -m neoos_autodev.cli check --repo PATH` and `python3 -m neoos_autodev.cli run-tests --repo PATH --state-dir PATH`.
  - Require an existing feature branch and clean worktree for `run-tests`; `check` remains read-only and can inspect any branch.
  - Create state/report files only inside an explicitly selected state directory; default to a project-local ignored directory and add that exact directory to `.gitignore`.
  - Do not implement AI patch generation, remote pushes, branch creation, merging, or deployment in this milestone.
- [ ] **Step 4: Run full local test suite**
  - Run: `python3 -m unittest tests_autodev -v`
  - Run: `python3 -m unittest test_neoos -v`
  - Expected: both PASS; existing NeoOS behavior remains unchanged.
- [ ] **Step 5: Update CI**
  - Add `python -m unittest tests_autodev -v` to `.github/workflows/ci.yml` alongside the existing test command; retain the current Python version matrix and job timeout.
  - Do not remove or weaken existing workflow checks.
- [ ] **Step 6: Update README**
  - Document the CLI as an opt-in local safety/test tool, the feature-branch requirement, and the fact that it does not provide 24-hour persistence if Android terminates the process.
  - Preserve the existing Podroid/Docker instructions and clearly label AI auto-edit and deployment as not yet implemented.
- [ ] **Step 7: Run final validation**
  - Run: `python3 -m unittest tests_autodev -v`
  - Run: `python3 -m unittest test_neoos -v`
  - Run: `git diff --check`
  - Run: `git status --short` and verify only the planned files changed.
  - Expected: all tests pass, diff check is clean, no secrets or unrelated changes are present.
- [ ] **Step 8: Commit the CLI milestone**
  - Commit message: `feat: add safe local autodev core cli`

## Scope Boundaries and Follow-Up Plans

This first plan delivers only the safe local execution foundation. It does not yet generate or apply AI-authored code changes.

Create separate plans after this milestone is reviewed and tested:
1. **AI task planning and patch application:** provider adapter, task decomposition, diff-size/path policy, isolated patch application, repair loop integration, offline/no-provider behavior, secret redaction.
2. **GitHub and CI integration:** explicit opt-in branch creation/push/PR flow, GitHub Actions result inspection, permissions and rate-limit handling.
3. **Deployment verification:** Vercel/Render read-only deployment checks and health verification; deployment execution remains approval-gated.

Do not implement these follow-up plans as part of this core milestone.

## Self-Review Checklist

- [x] Each design requirement maps to a task or an explicit follow-up plan.
- [x] The first milestone is independently testable and avoids AI/network dependencies.
- [x] Existing NeoOS simulator and Docker configuration are preserved.
- [x] Every component has failing-test, implementation, and passing-test steps.
- [x] Dirty workspace, invalid checkpoint, timeout, expired deadline, and path traversal have explicit tests.
- [x] No automatic merge, push, deployment, arbitrary shell command, or destructive Git command is included.
- [x] CI retains the current Python matrix and existing NeoOS test.
