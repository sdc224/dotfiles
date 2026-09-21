---
name: chrome-osascript-debug
description: Debug and inspect a live web app in the user's already-authenticated Google Chrome using AppleScript (osascript), instead of the isolated cursor-ide-browser tool. Use when a page requires SSO/enterprise login the automated browser can't pass (e.g. Intuit internal apps behind Enterprise SSO), or when the user says "use chrome browser, osascript way" / "use real chrome".
---

# Chrome debugging via osascript (real, authenticated Chrome)

## Why this exists

`cursor-ide-browser` runs an isolated Chrome profile with no session cookies.
Internal/enterprise apps behind SSO (e.g. `*.intuit.com` behind
`federatesys.intuit.com`) redirect it to a login wall it can't pass. The
user's real Chrome window already has a valid SSO session — drive that
instead via `osascript`/AppleScript.

**Precondition** (one-time, per AGENTS.md-style setup docs): Chrome → View →
Developer → **Allow JavaScript from Apple Events** must be enabled, or
`execute javascript` calls below fail silently.

## Project-specific live URLs

- **alp-console-ui** (this repo's UI, QAL environment, already authenticated
  in the user's Chrome): `https://idx-selfserve-qal.app.intuit.com/alp-console-ui/alp-console`
  — the Run List. Individual run detail pages are **client-side routed** (no
  URL change on navigation — see Known limitations below); either navigate
  there yourself by clicking a run row via `execute javascript`
  (`document.querySelectorAll('tbody tr')[i].click()`) or ask the user to
  navigate manually, then confirm you're on the right screen via a DOM probe
  (e.g. `document.querySelector('[data-testid=stage-stepper]')`) rather than
  trusting the URL.
  - To debug **local/uncommitted code changes** against this same QAL URL:
    run `yarn serve` (not `yarn start`) from the repo root (or the relevant
    `.worktrees/<slug>` checkout) — `plugin-cli serve` runs a local webpack
    dev server (self-signed HTTPS, e.g. `https://localhost:<port>/`, port is
    dynamic — check the process's listening socket with `lsof -i -P -sTCP:LISTEN`
    if needed) that the AppFabric shell page picks up as an override for the
    `alp-console-ui` plugin. Just start it, then navigate/reload the QAL URL
    above in real Chrome as normal — no separate localhost URL to visit, the
    QAL page itself renders your local build. Confirm you're seeing local
    code (not the deployed version) via a DOM probe for a feature you know
    only exists locally, not from the URL or title.

## Navigate to a URL (reuse existing tab if open)

```bash
osascript -e '
tell application "Google Chrome"
  activate
  if (count of windows) = 0 then make new window
  tell active tab of front window to set URL to "https://example.com/path"
end tell'
```

To reload after a local rebuild (e.g. webpack watch picked up a source change):

```bash
osascript -e 'tell application "Google Chrome" to tell active tab of front window to reload'
```

## Read/query the page — use `execute javascript`, not System Events

`execute javascript` runs in the real page context (no Accessibility
permission needed) and is the reliable way to inspect and interact:

```bash
osascript -e '
tell application "Google Chrome"
  tell active tab of front window
    execute javascript "document.querySelectorAll(\"[data-testid^=my-prefix]\").length"
  end tell
end tell'
```

- Escape inner double-quotes as `\"` inside the single-quoted `-e` string.
- Keep the JS itself as one expression/statement chain — the return value of
  the *last* statement is what comes back to the shell.
- `element.click()` works for triggering React `onClick` handlers (synthetic
  event delegation still fires on a real DOM `click()` call) — use this
  instead of simulated mouse/keyboard input.
- If `.click()` on a row/element does nothing, the handler is likely on a
  *nested* child (a button/svg inside the row), not the element you grabbed —
  query for `button, a, [role=button]` inside it first.

## Do NOT use System Events keystroke/click

`tell application "System Events" to keystroke ...` / `click at` requires
Accessibility permission for the terminal app, which is usually **not**
granted and fails with `osascript is not allowed to send keystrokes. (1002)`.
Scroll, click, and read through `execute javascript` instead
(`window.scrollBy(...)`, `el.click()`, `el.textContent`).

## Screenshot

Bring Chrome frontmost first, or `screencapture` captures whatever window
already has focus (which may be the IDE, not Chrome). `tell application
"Google Chrome" to activate` is **unreliable** in some sandboxed/remote
desktop setups (Chrome reports itself frontmost via `System Events`, but
`screencapture` still grabs the IDE window behind it). Prefer forcing
frontmost through `System Events` directly, which was consistently reliable:

```bash
osascript -e 'tell application "System Events" to tell process "Google Chrome" to set frontmost to true'
sleep 1
screencapture -x /tmp/name.png
```

If a screenshot still looks like the wrong app, sanity-check with
`osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true'`
before trusting the capture.

Then read the file with the image-reading tool to actually see it.

## Check the local dev server is still up

If a plugin/app is served locally (e.g. `plugin-cli serve` on a fixed port),
verify before debugging:

```bash
lsof -i :PORT
curl -sk https://localhost:PORT/ -o /dev/null -w "%{http_code}\n"
```

## Known limitations

- Client-side-routed apps (state-based navigation, no URL change on
  "navigate") won't show a new URL after a click — confirm via DOM query
  (`execute javascript`) rather than the URL.
- No way to hover-simulate via CDP-style mouse events through pure
  AppleScript; if a UI needs `:hover` or `mouseenter` to verify, either
  dispatch a synthetic event via `execute javascript`
  (`el.dispatchEvent(new MouseEvent('mouseenter', {bubbles:true}))`) or ask
  the user to check visually.
