# Validation — Module Studio 0.7.0

Added a single Windows Play Adventure launcher that readies AI Player, registers the matching module build and opens NWN. A New Adventure / Load Saved Game choice is offered in the same launcher. Native gameplay scripts/module bytes are unchanged for the existing errand release.

- **126 automated checks pass**, including startup readiness, timeout cleanup, key-presence/configuration errors, native build/sidecar matching, character-selection arguments, saved-game arguments, reused/owned service lifecycle, recovery after a reused service stops, duplicate-game prevention, offline bridge pausing, module backups, bundled-module installation, draft-safe registration and portable package privacy. Earlier native gameplay tests remain included.
- The real Play Adventure.cmd → PowerShell → Python path passes -CheckOnly against the installed rw_errands.mod. A completely extracted share ZIP also passes its bootstrap's -CheckOnly with matching module/project and paths containing spaces. These checks start neither NWN nor AI Player and make no OpenAI request.
- A real readiness/context-registration check against Studio 0.7 passed with the installed errand build; the authoring draft remained byte-identical. This check did not start NWN or make an OpenAI request.
- The game arguments were verified against the installed official NWN:EE v74 release notes, Patch 1.66: +LoadNewModule opens the module at premade character selection; +TestNewModule silently chooses the first character and is not used.
- New exports contain a module-specific Play Adventure.cmd, Start-Adventure.ps1 and AI Player runtime. Cached export refreshes update launcher files atomically without rewriting the native module. Packaging uses explicit runtime/source allowlists; player settings, environment files, logs and local histories are excluded.
- Registering a player's build context does not save/overwrite the author's project draft. Existing imported contexts are compared after schema migration; mismatched build IDs/context are refused before game launch.
- The launcher supervises its worker until the game exits, restarts a stopped worker up to three times, and stops only its own worker. An existing AI Player is reused. An active NWN game is never closed or duplicated, and a differing installed module is not replaced while NWN is running.
- No NWN or Aurora instance launched by the agent. Startup/game lifecycle tests use fake game processes; actual Windows/Steam launch, character selection, saved-game selection and sustained in-game responses remain for the user's test. Bridge readiness means local service plus key availability, not API credit/authentication validation.

## Existing trial preserved

- Module: rw_errands.mod
- Build: f0ba3e8e679884d13d20
- SHA-256: 3b8d67ab6b7907d08831872bb3bb16759885acbfc3eec2f92f1bb3521e7e6eb1
- The share ZIP now includes the launcher/runtime; its .mod remains byte-identical. No new game is required solely for the launcher. An older save still needs its own matching build context.

---

## Previous 0.6 validation record

# Validation — Module Studio 0.6.0

Added owner-directed companion inspection and NPC visit/return/report tasks. Supports recruitable party members and the actual owned familiars/summons; nonverbal profiles inspect without invented speech, while verbal visits require a speaking source profile.

- **105 automated checks pass**, including installed-game native compilation for AI-on/off modules and all earlier quest, merchant, companion, patrol/social and UI/speech checks. Added coverage for default-off migration, source/recipient opt-in, matching familiar/summon profiles, distinct actor identities, gated recipient knowledge, bounded answers, no mechanical model actions, bridge visit dispatch, native chest-open/ownership checks, order/permission/epoch guards, disappearance cleanup and return proximity.
- Browser verified source inspection/visit flags and recipient visit opt-in, saving disabled states and restoring the example, plus adventure review. No browser errors/warnings observed. The trial settings were restored to its factory example.
- One real recipient-answer request passed through the previously authorized OpenAI key: 1 request, 285 input tokens and 151 output tokens. The answer used Ilyra's scoped knowledge and action none. Synthetic actor identities were used; this was not an in-game travel/transport test.
- Inspection calls native interaction, requires confirmed GetIsOpen and immediate item ownership before observing contents, and contains no item-taking or reward functions. Opening unavailable containers fails without reading contents. Reports are bounded and flag omitted items.
- Visit transport starts only after arrival and native question speech. Target identity, life/control, opt-in, range, epoch/session/expiry and actual answer delivery are checked before return. Reports require the owner within five metres and LOS. No quest/merchant actions are applied.
- Associate movement uses a bounded lease of native follow/stay/guard flags. Restoration checks both the captured native command and control epoch. Cleanup defers for direct control and does not clear combat actions. Disappeared companions release recipient locks; newer native orders invalidate restoration.
- Studio 0.6 and AI Player are configured locally. No NWN/Aurora instance launched by the agent. Actual pathfinding, NPC chest interaction, recipient speech, cancellation and return timing remain the user's engine playtest.

## Installed trial

- Title: The Silent Bell — Companion Errand Trial
- File: rw_errands.mod
- Build: f0ba3e8e679884d13d20
- SHA-256: 3b8d67ab6b7907d08831872bb3bb16759885acbfc3eec2f92f1bb3521e7e6eb1
- 154 resources, 38 compiled scripts; 3 areas, 7 rooms, 7 NPCs, 2 quests.
- Source task permissions and AI recipients are enabled for the trial. Earlier installed trial modules and saves were preserved. Start a new game to receive the new scripts.

## Limits and acceptance

One task per owner; visible same-area targets within 45 metres; 240 active seconds overall and 90 wall-clock seconds for visit replies. Inspect only accessible unlocked/untrapped containers, no taking or recursive bag search. Visits ask a specific question or the picker default and report the actual answer without quest/reward changes. Source and recipient permissions default off in upgraded projects. Cross-area travel, lock/trap work, theft/item fetching, invisible recipients and unrestricted LLM planning remain unimplemented. Native compilation cannot prove engine action timing; PLAYTEST.md contains the required checks.

---

## Previous 0.5.1 validation record

# Validation — Module Studio 0.5.1

Fixes prompted by user playtest: yellow system-only NPC replies, missing/one-sided companion inventory display, and clipped native panels.

- **92 automated checks pass**, including installed-game native compilation, AI-on/off export and prior quest/merchant/companion/patrol/social regressions.
- Successful NPC/companion replies call SpeakString on the captured actual actor; failures remain SendMessageToPC. Existing ownership, pending-version and story-action guards remain.
- Panels now use an auto-scrolling native group and explicit row widths/heights. Companion windows and merchant windows are resizable. Group/text/row constructors were checked against the installed game's nw_inc_nui.nss via GameAssets; no external UI library or game asset edits.
- Inventory shows both sides concurrently with separate six-entry pages. It enumerates direct inventory plus equipped items, marks restricted entries instead of hiding them, and retains original-object/native transfer checks. Familiar/summon storage remains a distinct owner-held satchel.
- No NWN or Aurora instance launched by the agent, and no additional OpenAI request was needed for these fixes. Actual speech and panel rendering remain for the user's playtest; no claim of engine UI verification.

## Separate installed test build

- Title: The Silent Bell — UI & Speech Fix
- File: rw_ui_fix.mod
- Build: bd87aac992f04bec7956
- SHA-256: 68b9fd1d6722e934ee892287fbfccd7176333dd21bd5828c5029b0b011a0bf77
- 145 resources, 34 compiled scripts; 3 areas, 7 rooms, 7 NPCs, 2 quests.
- Prior installed trials and existing saves preserved. Start a new game to receive these scripts.

---

## Previous 0.5 validation record

# Validation — Module Studio 0.5.0

Added native same-area room patrols and optional two-sided public AI conversations for authored NPCs, with module/per-NPC creator switches. No NWNX or game/client binary changes.

- **90 automated checks pass**, including native AI-on/AI-off module compilation and the existing courier, quest, merchant and companion regressions. New checks cover migration with defaults off, reachable routes, bounds, mutual partner opt-in, profile/privacy isolation, finite non-mechanical responses, player-priority mailbox ordering, yielding between speakers, behavior generation scope, exact pending actor references, interruption/expiry checks and retained native heartbeat/combat.
- JavaScript syntax passes. Browser checks verified global and individual patrol/social switches, saved off states, restored on states, route reordering/restoration, character selection and adventure review. No browser warnings/errors observed. The trial's edited settings were restored. Tomas was subsequently given the same route as Mira to provide a shared meeting stop.
- **One real two-sided exchange passed** through the previously authorized OpenAI key: 2 requests, 608 input tokens and 275 output tokens. Speaker contexts are isolated and responses contain action none. This used synthetic actor identities, not a live NWN transport test.
- Native social delivery requires both actual actors, matching UUID/epoch, ownership/control/life/combat checks, range/LOS/perception and no active player request/conversation. Only emitted public lines are saved. Patrols use native ActionMoveToLocation, with bounded attempts and retries; no teleport.
- Studio 0.5 is running locally with AI Player enabled. Existing projects/builds were preserved. Existing projects migrate with ambient behavior disabled.
- No NWN or Aurora instance launched. Native pathfinding, speech rendering, interruption, native control and save/reload acceptance remain for the user. See PLAYTEST.md.

## Final installed trial

- Title: The Silent Bell — Patrol & Social Trial
- File: rw_ambient.mod
- Build: 96822e969406c35c49a4
- SHA-256: 4c05359609982e43a19a89003225002c5aabaa72f032d5502a61a3d1a8bcc625
- Contents: 3 areas, 7 rooms, 7 NPCs, 2 quests, 145 resources, 34 compiled scripts.
- Mira and Tomas have shared guest-hall/sanctuary patrol stops; both permit public conversation with each other.

## Remaining scope

This release supports authored unowned NPCs, same-area room-centre routes and short nearby exchanges. It does not add cross-area patrols, custom coordinate waypoints, travelling social visits, all-creature social adapters, autonomous town schedules or mechanical actions through social speech. Both NPC profiles must opt in; live social AI needs the player companion and key, while native patrols work offline. User playtesting is required before treating these behaviors as engine-verified.

---

## Previous 0.4 validation record

# Validation — Module Studio 0.4.0

Companion foundation: recruitable party members, existing native familiars and spell summons. No NWNX or game/client binary changes.

- **75 automated tests pass**. Includes native AI-on and AI-off compilation against the installed NWN:EE header/assets, legacy courier/quest/merchant regressions, project migration, profile precedence and validation, actor/owner checks, creator restrictions, secret filtering, finite model actions, mailbox companion dispatch, retained recruit equipment/combat scripts, save-local SQL/history and original-object inventory code.
- JavaScript syntax checks pass. Browser checks verified companion navigation, personality save/restore, custom template addition/removal, Seren's recruitment settings and adventure review. The trial's original settings were restored; no browser warnings/errors were observed.
- **2 live OpenAI companion checks passed** through the previously authorized key: a nonverbal cat follow request and an explicit Seren follow request. 1683 input tokens, 206 output tokens. These use synthetic native snapshots and prove model/adapter behavior, not in-game transport or movement.
- Studio 0.4 and the enabled AI Player are running on 127.0.0.1:8766. Existing local projects/builds were preserved.
- No NWN or Aurora instance was launched. The new module has **not** been played or opened in Aurora. PLAYTEST.md provides the user's acceptance procedure.

## Installed trial

- Title: The Silent Bell — Companion Trial
- Module: rw_companions.mod
- Build: ecc4ccf64e652d742433
- SHA-256: b6e7f047db7d33eaf8b2e198a800ba302a19d95f1d6fd85628c81438f1392a09
- Contents: 3 areas, 7 rooms, 5 NPCs, 2 quests, 135 resources, 32 compiled scripts.
- Installed as a separate file in the local NWN modules folder; prior courier and merchant trials preserved.

## Engine checks still required

Native UI rendering, recruitment/dismissal, party switching and possession, original familiar penalties, native combat, follow/stay/guard behavior and exit travel, resummoning/expiry, stale reply rejection, original-object Give/Take and stack merging, recoverable bags and save/reload. Native compilation/resource assertions cannot prove event timing or action-queue behavior. Inventory confirmation is observational; it never creates replacement items or retries automatically. If a transfer is unconfirmed, inspect actual inventories first.

Satchels are owner-held native containers, not familiar equipment slots. Memories are recent bounded dialogue, not full relationship simulation. Advanced errands, social visits, AI healing/spell/tactics, animal-companion and dominated-creature adapters remain unimplemented.

---

## Previous 0.3 validation record

# Validation — Module Studio 0.3.0

Scope: AI conversation and quest progression, plus native AI/menu merchants. Other AI NPC port features remain on the roadmap.

## Completed

- **61 automated tests pass**, including compilation against the installed NWN:EE header/assets with nwnsc 1.1.5. Native tests cover both AI-enabled and menu-only merchant builds, plus the legacy courier exporter.
- Story tests cover current-NPC action allowlists, prerequisites, branch selection, invalid model actions and native checks against changed objective state. All paths call the shared native quest/reward functions.
- Merchant tests cover upgrading old format-2 projects without mutating them, stock/price/haggle limits, real-observation quote grounding, sold-out stock, restricted model actions, exported inventory resources, native menu wiring and stack-safe delivery preparation.
- Native export verifies every GFF round trip and the MOD resource index. The stock test verifies 11 actual goods on Bram and both merchant menu scripts. Native UI and transactions use no NWNX functions.
- Delivery prepares one unit in an empty temporary native store before copying it into the buyer's inventory. This handles the documented CopyItem behavior of returning an existing merged stack, without resizing or overwriting that existing stack's quantity. Stock is reserved before delivery; failed delivery does not take gold. Exact engine behavior still needs playtesting.
- Native shop events check window token/generation, module-load session, actor, proximity, line of sight, combat, quote price, expiry, stock and funds. Purchases require a native Buy click; the AI has no direct payment/item-transfer action.
- Haggle rolls and offer duration are native. Offer state and stock follow the savegame; the duration counts active module-heartbeat seconds rather than wall time while paused.
- Three **real OpenAI checks passed** using the previously authorized key: an observed dagger price, a requested shop opening, and an explicit sealing branch choice. Total: 3 requests, 2254 input tokens and 287 output tokens. These were model/adapter checks, not an in-game transport test.
- Browser checks verified Bram's merchant card, quantities/prices, stock-line addition/removal, haggling toggle, saving, adventure review and native export. The original sample values were restored after editing. No browser errors or warnings were observed in the final check.
- JavaScript syntax checks pass. Local Studio 0.3 and its player companion are running on 127.0.0.1:8766. Existing local projects/builds were preserved in the Git checkout's ignored data folder.
- No NWN or Aurora instance was launched.

## Installed trial build

- Title: The Silent Bell — AI & Merchant Trial
- Filename: rw_ai_market.mod
- Build: 89751fbc24d1c1ca7a03
- Contents: 3 areas, 7 rooms, 4 NPCs, 2 quests, 112 native resources, 23 compiled scripts
- SHA-256: 71f904c83be6f100fb874256188ebc0722fd07f6fa31cdc9704c185c4eed460c
- Installed in the local NWN user modules folder. The original Missing Courier files remain separate.

## Required user verification

The trial has **not** been played or opened in Aurora. Native compilation and resource checks cannot prove game event timing or UI rendering.

Priority checks: native goods-panel rendering; exact gold/item transfer; potion merges; insufficient funds; sold-out stock; double clicks; offer expiry; AI/menu quest switching; pending-reply rejection; and save/reload before/after purchases and decisions. Also check walkability, exits, party travel, death/respawn and both endings. PLAYTEST.md contains the concrete procedure.

This first merchant release sells eight catalogue goods to players. Buyback, general barter, restocking, familiar/summon adapters, patrols and NPC-to-NPC conversations are not implemented in this release.

