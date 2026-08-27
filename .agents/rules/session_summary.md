---
trigger: model_decision
description: when said summary the session
---

# Session Summary Rule

At the end of every chat session (or when the user says "wrap up",
"summarize session", or "end session"), generate a comprehensive
summary and append it to `SESSION_LOG.md` in the project root.
Create the file if it doesn't exist.

The goal of this log is to let someone who was NOT present fully
reconstruct what happened in the session — what was wanted, what was
tried, what broke, what was decided, and where things stand. Prefer
completeness over brevity. Short bullet fragments are not enough;
write in full sentences where it aids understanding.

## File Structure

`SESSION_LOG.md` always has two parts, in this order:

1. **Index** — a single table at the very top of the file, under a
   `# Index` heading.
2. **Entries** — full session summaries, newest appended at the
   bottom, each separated by `---`.

## Index format

```markdown
# Index

| Date | Session Time | Goals | Status | Jump |
|------|---------------|-------|--------|------|
| 2026-08-27 | 14:30 | Fix auth bug; Add dark mode | ✅✅ | [#2026-08-27-1430](#2026-08-27-1430-session-summary) |
| 2026-08-26 | 09:10 | Refactor API client | ⚠️ | [#2026-08-26-0910](#2026-08-26-0910-session-summary) |

# Entries
```

- One row per session (not per goal). The **Goals** column lists each
  goal's short title, semicolon-separated.
- The **Status** column shows one status icon per goal in the same
  order (✅ done, ⚠️ partial, ❌ blocked), so a session with 2 done
  and 1 blocked shows `✅✅❌`.
- The **Jump** column links to an anchor matching that session's
  heading. Use a slug of the format `#YYYY-MM-DD-HHMM-session-summary`
  and give the entry heading a matching explicit anchor, since
  auto-generated heading anchors aren't reliable across renderers:

```markdown
### <a name="2026-08-27-1430-session-summary"></a>[2026-08-27 14:30] Session Summary
```

- Newest session goes at the **top** of the index table (reverse
  chronological), even though entries below are appended in
  chronological order at the bottom of the file.

## Format (one entry per session, multiple goals allowed)

```markdown
## [YYYY-MM-DD HH:MM] Session Summary

**Duration:** ~<estimate if known>
**Overview:** <2-4 sentence narrative of what this session was about
overall, why it happened (e.g. bug report, new feature, cleanup), and
how it went in general terms.>

**Goals:** <N> total — <count> done, <count> partial, <count> blocked

---

### Goal 1: <descriptive title>

**Status:** ✅ Done / ⚠️ Partial / ❌ Blocked

**Context:** Why this goal came up and what the user was trying to
achieve, in their own terms where possible.

**Approach / Plan:** Describe the finalized approach in enough detail
that someone could understand the reasoning, not just the label. If
the plan changed during the session, describe the evolution: what was
tried first, why it was abandoned or revised, and what the final
approach was (mark it `(final)`). If no explicit plan was needed
(trivial fix), say so briefly.

**Work Done:** Narrate what was actually implemented or changed, in
the order it happened. Include reasoning behind non-obvious choices,
not just the "what."

**Errors & Issues:** For each error encountered — the error/symptom,
what was tried to diagnose or fix it, whether it worked, and the root
cause if known. Include dead ends, not just the fix that worked;
they're useful context for next time.

**Files Touched:**
- `path/to/file` — what changed and why

**Outcome:** Where this goal stands at the end of the session, and
any relevant caveats (e.g. "works but untested on X", "fix is a
workaround, not a root-cause solution").

### Goal 2: <descriptive title>
... (same structure) ...

---

### Open Threads / Next Steps
Anything left incomplete, deferred, or flagged for later — across all
goals. Include unresolved errors, follow-up ideas the user mentioned
in passing, and anything explicitly postponed.

---
```

## Rules

1. Always use the real current date/time — never placeholder or guessed timestamps.
2. Treat each distinct user request/task in the session as its own **Goal** block, even if related. Don't merge unrelated asks into one goal.
3. Favor clarity and completeness over conciseness in entry bodies. It's fine for a goal's writeup to be several paragraphs if the work was substantial.
4. Log every error/exception per goal, even if resolved — include the diagnostic path, not just the final fix.
5. Never overwrite previous entries — always append new entries at the bottom of the Entries section.
6. If a goal involved no code changes (pure Q&A/discussion), omit Files Touched but still fill in Context and Outcome — discussions matter too.
7. If only one goal existed, still use the "Goal 1" format for consistency.
8. Don't ask for confirmation before writing the log unless the user explicitly disabled auto-logging.
9. Describe finalized plans with actual reasoning, not just a label ("used Redis for caching" is not enough — explain why Redis was chosen over alternatives, if that was discussed).
10. The **Goals** rollup line in the entry must match the sum of goal statuses exactly.
11. Write the Overview section last, after all goals are documented, so it accurately reflects the full session.
12. **Every time an entry is appended, also add a matching row to the top of the index table** — never write an entry without updating the index in the same operation.
13. If `SESSION_LOG.md` doesn't exist yet, create it with the `# Index` heading, an empty table (header row only), and a `# Entries` heading before appending the first session.
14. Never reformat, reorder, or delete existing index rows or entries — only ever add new ones.