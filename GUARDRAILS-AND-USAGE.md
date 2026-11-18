# Gameplay guardrails and token usage

Open **Guardrails & usage** in the Studio sidebar, or follow the link on **AI service status**. These controls belong to this service installation, not to an individual module. They work with both OpenAI and Gemini. Saving settings affects new requests; it does not cancel requests already running.

## Gameplay protection

Guardrails AI 0.11.0 runs custom local validators adapted from the Role Weaver Server Addon. There is no additional model judge, remote validation, telemetry, or automatic re-asking. Validation history is cleared after every check. SDK checks are enabled by default and fail closed if the SDK is unavailable or validation fails. Turning SDK validation off keeps the built-in policy checks active.

The policy checks live NPC and merchant dialogue, companions, companion visits, ambient NPC conversations and the AI DM. It detects common instruction overrides, prompt disclosure, out-of-character software references, malformed or oversized text, credential-like strings and optional blocked phrases. Email/phone masking can be enabled for inputs and replies containing them replaced. Matching is heuristic: it cannot guarantee safe content or factual/lore accuracy. Existing schema checks and native quest, inventory and merchant action validation remain authoritative.

A rejected input costs no provider call. A rejected output becomes a short in-character response with **all proposed actions cleared**. Nonverbal companions receive a nonverbal fallback. Rejected outputs still count toward token usage because the provider already generated them. Module creation does not use these gameplay dialogue filters.

Defaults are 12 gameplay calls/minute, 60/hour and at most 1,400 output tokens per call. Ambient conversations can be paused globally. A single NPC-to-NPC exchange can use two calls. Daily token stops are optional (0 disables) and reset at midnight UTC. They stop new calls when reported input + output tokens reach the threshold; calls already in progress can exceed it. When a daily stop is enabled, completed calls with missing usage pause new gameplay calls rather than being treated as free. Interrupted calls become unknown failures after 15 minutes. Provider billing controls remain separate.

## Usage report

The report separates **Gameplay** and **Module creation**, with input/output tokens, cached input and reasoning output, API calls, blocked calls, replaced replies and failures. Cached and reasoning tokens are already included in input/output totals, not added twice. Gemini thinking tokens are included in output. Provider/model totals and daily UTC bars can be viewed over the last hour, 24 hours, 7, 30 or 90 days. Use **Refresh usage** to see newly completed calls.

Tracking begins with this update; earlier calls cannot be reconstructed. Counts come from provider responses, including incomplete, refused or invalid results where usage was supplied. Missing counts remain unknown and totals are marked partial. This is a token report, not a monetary invoice or a provider-account-wide total. Requests from other applications are not included.

Settings are saved in `guardrails.json`; usage in `ai-usage.sqlite3`, within the service workspace. Records are retained for 90 days. The database stores timestamps, scope, provider/model, counters and status/category codes; no prompts, replies, player names or credentials. These files are excluded from normal source releases, installers and shared adventures. Restarting the service preserves both settings and usage.

## Source installations

Windows installer builds bundle Guardrails AI and its dependencies; no separate Python setup is needed. Developers using the source checkout/ZIP need Python 3.10–3.13 and must create a local environment once:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-guardrails.txt
```

Then run **Start Role Weaver.cmd**. The source launcher prefers `.venv`. For the source fallback in an adventure ZIP, run these commands inside `AI Player`. An installed Studio is preferred by the adventure launcher.

The installer build downloads compatible Windows wheels, includes their package license notices, and verifies the embedded runtime can validate text with external network connections disabled. Published installers are unchanged until a new release is built.
