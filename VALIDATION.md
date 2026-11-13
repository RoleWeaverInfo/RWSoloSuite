# Validation — 2026-11-13

Release: Role Weaver Module Studio 0.2.0, initial authoring/playtest release.

## Completed

- **43 automated tests passed**, including native compilation of ordinary and optional-AI adventures and regression coverage for the earlier courier edition.
- Adventure checks cover requested room counts, bounds, connected rooms, conflicting ports, cross-area exits, one-way return paths, quest references, branches, cycles, prerequisite deadlocks and consumed quest items. AI proposal tests cover scope enforcement, one repair attempt and NPC secret gating.
- The native terrain test compares every generated tile's rotated corner types with the installed NWN tileset definitions. This checks the terrain construction, but does not run the engine's walkmesh.
- Export tests reparse and round-trip every generated GFF resource and compare the MOD index/payload with the export input. Branches compile into native conversation actions/conditions and journal entries. Standalone exports contain no SQL mailbox or NWNX dependency.
- Optional-AI exports compile and retain the native quest engine. Transport tests cover old sessions, expired requests, paused companions, command allowlists and transaction cleanup. HTTP tests cover local host/origin/token checks, import/save, invalid paths and secret-free state.
- A **real AI authoring request** used a short observatory story plus a configured 14×10-tile, two-room dungeon. It generated two NPCs, two encounters, furnishings and a six-objective quest with two decision outcomes. The final successful request needed no repair. The resulting proposal passed validation and exported. During review, sample prose claiming that the puzzle physically unlocked a chest was corrected to match the implemented mechanics; the original response remains in data/authoring-validation/proposal.json.
- Browser checks verified the new authoring navigation, new project creation, a four-room layout, three corridor connections, saving, quest branch controls, adventure checks and native export. Both sample projects appear in the final editor. The previous global-name JavaScript error was corrected; the final views and actions worked.
- JavaScript syntax and the PowerShell launcher parse checks passed. The local server is running on 127.0.0.1:8766.
- No NWN game or Aurora instance was launched for these checks.

## Final ordinary-play examples

| Adventure | Build | Areas / rooms / quests | Native resources | Compiled scripts |
|---|---|---|---|---|
| The Silent Bell | d4d90eb04ef8f6b07c2e | 3 / 7 / 2 | 89 | 18 |
| The Starlight Trial | 07280a21ba675c01b460 | 1 / 2 / 1 | 63 | 19 |

SHA-256:

- rw_silent_bell.mod: 40b5285a875d6225ccacd551b98a8e59b331b9818d615005b9eaa7b8caa322e4
- starlight_trial.mod: 3b6d40d85409a99d26557acc93bf128828f3014e38740499ce41d53e26b41383

The share ZIPs include the module, editable project, native source, layout, validation report and instructions. The application package uses explicit source/example allowlists, excluding local settings, runtime databases and environment files, and scans candidates for the configured credential.

## Still requires the user's playtest

- Opening, editing and saving both new modules in Aurora.
- Walking every room/corridor, reaching placed objects, using both forms of exit, and checking party travel/control.
- Native dialogue and journal event timing, both quest endings, rewards, death/respawn and save/reload behavior.
- Actual encounter difficulty with different parties; count scaling is only a starting heuristic.
- Optional in-game SQLite exchange, live NPC/DM responses, secret unlocks and stale-reply handling in the engine.
- Playing a shared module on another NWN:EE installation without the authoring application.

Compilation, simulated transport tests and resource validation do not prove in-game behavior. See PLAYTEST.md for the concrete procedure. The existing Missing Courier modules remain separate from these new examples.

