---
name: review-github-pr
description: Review GitHub PRs by fetching diffs and existing comments via the DAST MCP (user-DAST-Orch), reading the local codebase for context, and adding concise human-sounding inline review comments to a pending review without submitting. Use when the user asks to review a PR, look at a pull request, or add review comments on GitHub.
---

# GitHub PR Review

## MCP Tool Setup

Use the **`user-DAST-Orch`** MCP server for all GitHub operations. Always read the tool schema before calling it:

```
/Users/schatterjee10/.cursor/projects/.../mcps/user-DAST-Orch/tools/<tool-name>.json
```

Key tools needed: `get_pull_request`, `get_pull_request_files`, `get_pull_request_reviews`, `get_pull_request_review_comments`, `create_pending_pull_request_review`, `add_comment_to_pending_review`, `delete_pending_pull_request_review`.

The repo owner is always `idx-docmgmt`, repo is `llm-orchestrator-service`.

---

## Workflow

### Step 1 — Fetch PR context (parallel)

```
get_pull_request          → title, description, head SHA, changed files summary
get_pull_request_files    → per-file diffs (patches with line numbers)
get_pull_request_reviews  → existing reviews (check for your own pending review)
get_pull_request_review_comments → existing inline comments (including bot comments)
```

### Step 2 — Read codebase for context

For each changed file, read the **current local version** of the file (not just the diff). This is critical — comments must reflect how the change fits into the broader codebase, not just the diff in isolation.

Focus on:
- Interfaces/abstract classes that changed
- Callers of changed methods to check for unintended side effects
- Config classes to understand how settings propagate
- Related mock/real implementation pairs

### Step 3 — Handle existing pending review

Check if you already have a pending review (`state: "PENDING"` in `get_pull_request_reviews` for your user). If the commit SHA differs from the current head SHA, **delete it first** with `delete_pending_pull_request_review`, then create a fresh one.

```
create_pending_pull_request_review  →  commitID: <head SHA from get_pull_request>
```

### Step 4 — Add inline comments

Use `add_comment_to_pending_review` for each issue found. Line numbers must match the **new file** line numbers (not diff line numbers).

**Computing line numbers from patch hunks:**
- `@@ -old_start,old_count +new_start,new_count @@` → additions in this hunk start at `new_start` in the new file
- Count down through context lines (+) and added lines to reach the target line
- Use `side: "RIGHT"` for new code additions, `side: "LEFT"` for removed lines
- Use `subjectType: "LINE"` for line-level, `subjectType: "FILE"` if unsure of exact line

**Never submit** — always leave the review in pending state for the user to review and submit.

---

## What to Look For

Prioritize real issues over style nits. In order of importance:

1. **Logic bugs** — conditions missing checks (e.g., gating delay but not the actual mock response on the same flag), missing null guards, incorrect fallback behavior
2. **Dead code / unused additions** — methods added to interfaces but never called in the real implementation (the caller still passes the uncleaned data)
3. **Type hint accuracy** — `type | None` when `Callable[[], Any] | None` is more accurate
4. **Resource waste** — creating expensive resources (e.g., connection pools, HTTP clients) that are never used in a given code path
5. **Inconsistency between similar implementations** — if two classes handle the same scenario differently without a reason

Skip: formatting, docstring completeness, minor naming preferences.

---

## Comment Style

Comments must sound like a teammate, not a report:

**Good:**
> The delay is gated on `enabled` but the response load below isn't — if `enabled=False` but `response_key` is set, this still returns a mock. Should probably mirror how `MockLLMProxy.ainvoke` handles it.

**Bad:**
> This code has a potential logic issue. The `mock_config.enabled` flag is checked for the delay simulation functionality at line 40, however the response_key check at line 45-47 does not include a corresponding check for the `enabled` flag. This creates an inconsistency where...

Rules:
- One or two sentences max for simple issues, three for complex ones
- Reference specific class/method names from the codebase (`MockLLMProxy`, not "the other mock implementation")
- Say what's wrong and what it should be — skip lengthy explanation of why
- No bullet lists inside a single comment

---

## Example Comment Bodies

```
# Type hint issue
`type` is too broad here — this is really a `Callable[[], Any]` (a factory), not a class.
`Callable[[], Any] | None` would be more accurate and `Callable` is already imported here.

# Dead method
This method is defined but never called in `GenOSRegistryClient`. The `mock_config` object
ends up in `_hydrate_parameters` via `parameters_with_mock` anyway and gets passed into
`str.format(**parameters)`. Python silently ignores extra kwargs so it won't break, but the
cleaning method seems to have been added with the intent to use it there.

# Resource waste
Even in mock mode, the `httpx.AsyncClient` connection pool is still created in `__init__`
but never actually used — `MockChatOpenAI` doesn't make HTTP calls. Minor, but worth noting
if you want to skip the connection setup when `llm_factory` is provided.
```

---

## Checklist Before Finishing

- [ ] Deleted stale pending review (if old commit SHA) and created fresh one
- [ ] Read local codebase files, not just the diff
- [ ] Checked bot/existing review comments — don't duplicate them
- [ ] Line numbers verified against patch hunk math
- [ ] Comments are concise and reference real class/method names
- [ ] Review is left in **pending** (not submitted)
