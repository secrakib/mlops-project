---
trigger: model_decision
description: when said summary the session
---

# Session Summary Rule

At the end of every chat session (or when the user says "wrap up", "summarize session", or "end session"), generate a comprehensive summary and append it to `SESSION_LOG.md` in the project root. Create the file if it doesn't exist.

The goal of this log is to let someone who was **NOT present** fully reconstruct what happened in the session — what was wanted, what was tried, what broke, what problems were encountered, how they were solved, what was decided, and where things stand. Prefer completeness over brevity. Short bullet fragments are not enough; write in full sentences where it aids understanding.

## File Structure

`SESSION_LOG.md` always has two parts, in this order:

1. **Index** — a single table at the very top of the file, under a `# Index` heading.
2. **Entries** — full session summaries, newest appended at the bottom, each separated by `---`.

## Index format

```markdown
# Index

| Date | Session Time | Goals | Status | Jump |
|------|---------------|-------|--------|------|
| 2026-08-27 | 14:30 | Fix auth bug; Add dark mode | ✅✅ | [#2026-08-27-1430](#2026-08-27-1430-session-summary) |
| 2026-08-26 | 09:10 | Refactor API client | ⚠️ | [#2026-08-26-0910](#2026-08-26-0910-session-summary) |

# Entries
```

* One row per session (not per goal). The **Goals** column lists each goal's short title, semicolon-separated.
* The **Status** column shows one status icon per goal in the same order (✅ done, ⚠️ partial, ❌ blocked), so a session with 2 done and 1 blocked shows `✅✅❌`.
* The **Jump** column links to an anchor matching that session's heading. Use a slug of the format `#YYYY-MM-DD-HHMM-session-summary` and give the entry a matching explicit anchor, since auto-generated heading anchors aren't reliable across renderers:

```markdown
### <a name="2026-08-27-1430-session-summary"></a>[2026-08-27 14:30] Session Summary
```

* Newest session goes at the **top** of the index table (reverse chronological), even though entries below are appended in chronological order at the bottom of the file.

## Format (one entry per session, multiple goals allowed)

```markdown
## [YYYY-MM-DD HH:MM] Session Summary

**Duration:** ~<estimate if known>

**Overview:** <2-4 sentence narrative of what this session was about overall, why it happened (e.g. bug report, new feature, cleanup), what problems arose, how they were handled, and how it went in general terms.>

**Goals:** <N> total — <count> done, <count> partial, <count> blocked

---

### Goal 1: <descriptive title>

**Status:** ✅ Done / ⚠️ Partial / ❌ Blocked

**Context:** Why this goal came up and what the user was trying to achieve, in their own terms where possible.

**Approach / Plan:** Describe the finalized approach in enough detail that someone could understand the reasoning, not just the label. If the plan changed during the session, describe the evolution: what was tried first, why it was abandoned or revised, and what the final approach was (mark it `(final)`). If no explicit plan was needed (trivial fix), say so briefly.

**Work Done:** Narrate what was actually implemented or changed, in the order it happened. Include reasoning behind non-obvious choices, not just the "what."

**Problems Faced & Solutions:** Document every meaningful problem encountered during this goal and explain how it was addressed. For each problem, include:
- **Problem:** What went wrong, what symptom appeared, or what limitation was encountered.
- **Diagnosis:** What was investigated or tried to determine the cause.
- **Solution:** What change, workaround, decision, or action resolved the problem.
- **Result:** Whether the solution worked, partially worked, or remained unresolved.
- **Root Cause / Lesson:** The underlying cause when known, or the key lesson/context that would help someone avoid or troubleshoot the same issue later.

Do not only describe successful fixes. Include dead ends, failed attempts, unexpected behavior, blocked approaches, and problems that were ultimately worked around. If the same problem required multiple attempts, record the progression and explain why earlier attempts were rejected.

**Errors & Issues:** For each error or exception encountered — the exact error/symptom where available, what was tried to diagnose or fix it, whether it worked, and the root cause if known. This section should capture technical errors and exceptions that may be useful for future debugging, while **Problems Faced & Solutions** should capture the broader obstacles, decisions, and practical difficulties encountered during the work.

**Files Touched:**
- `path/to/file` — what changed and why

**Outcome:** Where this goal stands at the end of the session, and any relevant caveats (e.g. "works but untested on X", "fix is a workaround, not a root-cause solution").

### Goal 2: <descriptive title>
... (same structure) ...

---

### Open Threads / Next Steps

Anything left incomplete, deferred, or flagged for later — across all goals. Include unresolved errors, unsolved problems, follow-up ideas the user mentioned in passing, and anything explicitly postponed.

---
```

## Rules

1. Always use the real current date/time — never placeholder or guessed timestamps.
2. Treat each distinct user request/task in the session as its own **Goal** block, even if related. Don't merge unrelated asks into one goal.
3. Favor clarity and completeness over conciseness in entry bodies. It's fine for a goal's writeup to be several paragraphs if the work was substantial.
4. Log **every error, exception, and meaningful problem per goal**, even if resolved. Record the diagnostic path, attempted solutions, final solution, outcome, and root cause or lesson when known.
5. Never overwrite previous entries — always append new entries at the bottom of the Entries section.
6. If a goal involved no code changes (pure Q&A/discussion), omit Files Touched but still fill in Context, Problems Faced & Solutions when applicable, and Outcome — discussions matter.
7. If only one goal existed, still use the "Goal 1" format for consistency.
8. Don't ask for confirmation before writing the log unless the user explicitly disabled auto-logging.
9. Describe finalized plans with actual reasoning, not just a label ("used Redis for caching" is not enough — explain why Redis was chosen over alternatives, if that was discussed).
10. The **Goals** rollup line in the entry must match the sum of goal statuses exactly.
11. Write the Overview section **last**, after all goals are documented, so it accurately reflects the full session, including the problems encountered and their resolutions.
12. **Every time an entry is appended, also add a matching row to the top of the index table** — never write an entry without updating the index in the same operation.
13. If `SESSION_LOG.md` doesn't exist yet, create it with the `# Index` heading, an empty table (header row only), and a `# Entries` heading before appending the first session.
14. Never reformat, reorder, or delete existing index rows or entries — only ever add new ones.
15. **Problems and solutions must be documented explicitly, not implied.** For every meaningful obstacle, state what the problem was and how it was solved or handled.
16. **Distinguish problems from errors.** A problem may be a design constraint, failed approach, ambiguity, missing dependency, unexpected behavior, or workflow obstacle even when no exception occurred.
17. **Record failed attempts and dead ends.** Do not hide unsuccessful approaches merely because the final solution worked.
18. **Preserve the reasoning behind solutions.** Explain why the chosen solution resolved the problem and, where relevant, why other approaches were rejected.
19. **Be specific enough to reproduce the troubleshooting path.** A future reader should be able to understand what happened, what was tested, and what ultimately fixed or bypassed the issue.
20. **Do not invent problems or solutions.** Only document issues that actually occurred in the session. When no meaningful problems occurred for a goal, explicitly state: "No significant problems were encountered."

## Required Problem/Solution Pattern

Every goal must use this pattern when problems occurred:

```markdown
**Problems Faced & Solutions:**

**Problem 1 — <short title>**
- **Problem:** <what happened>
- **Diagnosis:** <what was investigated or tried>
- **Solution:** <what resolved or mitigated it>
- **Result:** <final result>
- **Root Cause / Lesson:** <cause or useful takeaway, if known>

**Problem 2 — <short title>**
- **Problem:** ...
- **Diagnosis:** ...
- **Solution:** ...
- **Result:** ...
- **Root Cause / Lesson:** ...
```

When no meaningful problem occurred:

```markdown
**Problems Faced & Solutions:** No significant problems were encountered.
```
