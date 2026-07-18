# T63 Full Suite Regression Sweep After Profile Policy Change

## Metadata
- Status: Done
- Priority: P1
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Operator requested full-suite revalidation after recent command-profile policy
changes and reported suspicion of newly introduced test regressions.

## Objective
Run the full test suite and fix any regressions introduced by recent changes.

## Scope
- Execute full `unittest` suite under `tests/`.
- Fix failing tests caused by recent profile-policy work.
- Keep fixes minimal and scoped to failures.

## Non-Goals
- No unrelated refactors.
- No behavior changes outside regression fixes.

## Target Files
- tests/**
- lllars_core/** (only if required by failing tests)

## Verification
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\

## Rollback
Revert only the regression-fix changes if they prove incorrect.

## Completion Artifact
Passing full suite with focused regression fixes.

## Completion Notes
- Full suite initially failed on
	`test_runtime_api_submission.RuntimeApiSubmissionTests.test_submit_accepts_extended_run_fields_in_request`
	with HTTP 422.
- Root cause: shared test helper `extended_run_payload()` required external
	profile file resolution in an API test context that does not provide
	`command_profiles_path` resolution roots.
- Fix: reverted helper to `command_profile="none"` and removed
	`command_profiles_path` dependency in `tests/runtime_api_test_support.py`.
- Re-ran full suite; all tests pass.
