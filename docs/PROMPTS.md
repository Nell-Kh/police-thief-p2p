# Prompts Book (ספר הפרומפטים) — AI-Assisted Development Log

Per guidelines §8.3: a log of all significant prompts used to build this project, their context,
goal, outputs, and iterative improvements. Maintained continuously; finalized at submission.

**Toolchain:** Claude (Cowork agent mode) orchestrating file tools, shell, subagents and tests.
The human (nell) directs, reviews and approves; the agent plans, generates and verifies.

---

## Entry 1 — Source-document digestion
- **Context:** project start; two governing PDFs (160-page rulebook, 39-page guidelines).
- **Prompt (essence):** "Read both PDFs completely and produce exhaustive digests: every
  mandatory rule vs recommendation, the full mandatory parameters table verbatim, all protocol
  details, formulas, schemas and checklists; verify tables/numbers against rendered PDF pages."
- **Output:** three digest documents (ch. 1-7; ch. 8-11+appendices; guidelines) used as the
  compliance source of truth for all subsequent work.
- **Lesson:** digesting the normative appendices (ה, ו) verbatim first prevents value drift in
  every later artifact — all config values trace to Appendix ו.

## Entry 2 — Documentation-first scaffolding
- **Context:** guidelines ch. 2 mandates PRD → PLAN → TODO → per-mechanism PRDs, approved before
  any code.
- **Prompt (essence):** "Scaffold the uv project (ruff/coverage gates per guidelines ch. 6-8),
  config skeleton mirroring the parameters table, then write PRD.md, PLAN.md (C4 + ADRs),
  TODO.md (~60-commit roadmap), and seven mechanism PRDs consistent with the master docs."
- **Output:** repo skeleton + 10 documents; ADRs recording the dev-repo-split decision, the
  enhanced-heuristic strategy track, and the claude_api-with-template-fallback verbal layer.
- **Lesson:** encoding the seven rulebook development priorities directly as PRD files + TODO
  phases keeps the commit history aligned with the mandated process.

*(Entries continue as development proceeds.)*
