# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Skills & Workflow

This project uses **Superpowers skills** and **OpenSpec**. Before any task:

- Invoke the `using-superpowers` skill at session start — it governs all workflow decisions.
- For new features/changes: use `openspec-propose` → `openspec-apply-change` → `openspec-archive-change`.
- For exploration/design: use `openspec-explore`.
- For bugs: use `systematic-debugging` before proposing fixes.
- For any implementation: use `test-driven-development`.

OpenSpec changes live in `openspec/changes/`. The active v1 implementation plan is at `openspec/changes/v1-implementation/`.

## Project Docs

Full architecture, DB schema, MCP contract, configuration, and business rules are in `docs/`. Business rules for LLM context are in `rules/` — keep them there, not in Python code.
