# Portable jidou Implementation Plan

**Goal:** Add a runnable local backend shared by Codex, Claude Code and TRAE, with native Windows/macOS reminder integration while preserving the existing cloud adapter.

**Architecture:** Keep the standard SKILL.md entrypoint and 21 business fields. Add a SQLite-backed Python CLI with explicit initialization, parameterized CRUD, transactional identifiers and a reminder outbox. Separate time calculation, storage, notification delivery and platform installation. Never silently switch an existing cloud store to local data.

**Tech Stack:** Python 3.10+, SQLite, zoneinfo, existing PyYAML; optional lunardate for lunar recurrence. unittest and isolated temporary directories for verification.

## 1. Local storage and CLI

Write failing tests for explicit initialization, original text, independent status, atomic batches, operation-key conflicts, pagination, filtering, export/import and concurrent lineage allocation. Implement scripts/jidou_runtime/store.py and scripts/jidou.py. Run tests and real CLI smoke operations in a temporary home.

## 2. Scheduling and durable reminders

Write failing tests for due windows, quiet hours, per-record mute, fixed/custom lead time, daily/weekly/monthly/annual/interval recurrence, invalid local times and completion/undo. Implement schedule.py and outbox processing with SQLite transactions. Notification acceptance is not proof that a user read a message; document nontransactional delivery retries.

## 3. Agent and operating-system integration

Write failing tests for Codex/Claude/TRAE destinations, full package copying, existing unmanaged directories, shell-safe native command arguments and launch/task definitions. Implement explicit install and scheduler plan/apply entrypoints. Do not install into real user profiles or register real system tasks during development.

## 4. Optional native command execution

Add explicitly configured argv-only jobs with durable execution claims and no automatic retries for uncertain actions. Test with harmless local Python commands. Existing platform-specific API/skill execution remains available through the cloud adapter.

## 5. Documentation and release

Update backend selection, portable commands, dependency/setup instructions, migration boundaries and capability reporting. Keep schema properties identical. Run all regressions, official SKILL validator, independent review and isolated CLI acceptance checks. Record which native integrations are only definition-tested and which are executed on the Windows host. Publish the checked package and keep existing real data/tasks untouched.
