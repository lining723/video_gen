# Diff Scope Rules

These rules apply to every reviewer. They define what is in scope versus pre-existing context.

## Scope Discovery

Determine the diff to review using this priority order:

1. User-specified scope (`BASE:`, `FILES:`, `DIFF:`)
2. Working copy changes
3. Unpushed commits vs resolved base branch

The scope step in `review.md` handles discovery and passes the resolved diff. Reviewers do not need to discover it themselves.

## Finding Classification Tiers

### Primary (directly changed code)

Lines added or modified in the diff. Main focus.

### Secondary (immediately surrounding code)

Unchanged code within the same function, method, or block as a changed line. Report it when the change makes the issue newly relevant.

### Pre-existing (unrelated to this diff)

Issues in unchanged code that the diff did not touch and does not interact with. Mark these as `pre_existing: true`.

### Submodule-internal (code inside changed submodules)

Lines changed inside a submodule whose pointer was modified in the parent diff. Treated as Primary scope because the parent commit intentionally updates the submodule reference. Includes both committed changes (visible via the submodule's own `git diff <sub_base>`) and uncommitted dirty-state changes (visible via `git diff` / `git diff --cached` inside the submodule).

### Submodule-pre-existing (unchanged submodule code)

Issues in a submodule whose pointer was NOT changed in this diff. Mark these as `pre_existing: true`.
