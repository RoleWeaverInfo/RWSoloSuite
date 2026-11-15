# Module Studio 0.10.2 validation

## Current trial: companion packs and chest collection (0.10.2)

Validation: the full suite passed **162 tests**. After final recovery-menu and launcher edits, the affected suites passed another **28 checks**. The installed build `bb0a32903a9765136def` contains **44 compiled scripts / 170 resources**. Launcher CheckOnly found the installed module and matching project; AI Player 0.10.2 restarted with its existing key available and bridge enabled. No NWN or Aurora playtest was performed by the agent.

Start a **new game** in **The Silent Bell - Companion Pack Trial** (`rw_packfix.mod`) with AI Player 0.10.2. Older modules and saves are preserved.

The failed potion errand was rejected by an owner-distance check even though the companion had reached the chest. Collection now requires the companion at the accessible chest, not the player. Whole items/stacks go to a persistent companion pack, using a save-local escrow and confirmed destination counts. Item properties and local variables are copied; object identity changes. Ambiguous delivery stops rather than retrying a possible duplicate. Inspection alone never takes items.

**Companion pack - item grid** opens a normal placeable inventory through the player's native chest interaction. It is separate from equipped creature gear and legacy satchels. Use **!companions → Recover companion packs / old satchels** after dismissing a companion. Native merchant stores are unchanged.

Playtest: summon Agathos; open its pack; drag an ordinary item in and out. Stand away from the healing chest, ask Agathos to inspect it, then ask it to collect the entire healing-supplies stack. After the confirmed report, check the chest is empty and the pack contains exactly three supplies. Save/reload and dismiss/resummon to check recovery. Check Bram's shop still opens. GUI interaction, actual transfers and save/reload need the user's in-game verification; compilation alone does not prove them.

## Previous trial: familiar inventory and merchant conversation fix (0.10.1)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Familiar and Merchant Fix** (`rw_tradefix.mod`). Existing modules/saves are preserved. The backend merchant correction also applies to existing rw_trade saves; the native familiar menu changes require a new game in this trial.

The merchant error was a conversation-processing bug, not a missing build: merchant policy was removed from the NPC profile before native stock context read it. The profile is now sanitized after stock context is prepared. Bridge errors distinguish build-loading failures from failures processing a conversation; sanitized diagnostics contain request/build identifiers and exception type, never dialogue or credentials.

**Companion inventory - item grid** now targets the actual party member or familiar (including Agathos), rather than redirecting familiars to the player's inventory. **Recoverable satchel - in your inventory** is a separate, explicitly labelled option; open the named bag in your own inventory. Items placed directly on a familiar are not covered by satchel recovery. Summons use the paired storage list instead of unexpectedly opening only the player inventory. A native summon two-pane item grid is not implemented.

Validation: **162 tests passed**, including a regression through native merchant dialogue, error classification, familiar-versus-satchel dispatch and native compilation (**44 scripts**). The recorded failed rw_trade merchant payload was replayed locally with a stubbed provider: it reached the provider request step successfully; no API call was made and no game state changed. Native familiar inventory rendering and trading still need the user's in-game check.


Current build: `dcab39a773d509876f2e`. SHA256: `414d2315320fc59dbec25a73221041f94c98352dbcf49aeaa999db3062f758d8`.

## Previous trial: visual companion storage and merchant trading (0.10.0)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Visual Trading Trial** (`rw_trade.mod`). This module needs AI Player 0.10.0+ for live merchant conversation. Old modules and saved games are preserved; start a new game to receive the new store resources.

Companions retain **Inventory - item grid**, **Satchel - item grid**, and the text-list fallback. Speak to Bram and choose **Browse goods**, or ask him through AI chat, to open NWN's native store with item icons and normal buy/sell controls. Use its item drag-and-drop and trade confirmation controls. NWN handles the original stock, player belongings and gold. Test one purchase and one sale, reopen the store, and save/reload to check persistence.

Native store prices use NWN item values and Appraise. Haggling supplies a bounded discount to the native store opening; its displayed prices remain authoritative. A discount applies for that open window; reopening checks the offer timer. AI dialogue lists observed store goods, including player buybacks, but does not invent an exact final price. Stock is finite with no automatic replenishment. These stores have unlimited buying funds, pay at most 5,000 gold per item, and charge 100 gold for native identification; NWN enforces its normal eligibility rules.

In Module Studio, **Characters → Merchant shop → Shop interface** selects **Native visual store - buy and sell** or **Text list - fixed prices, buy only**. New merchant definitions default to native. Existing projects without this field remain list shops to preserve authored prices. The per-item price fields apply only to list shops; native pricing does not silently promise those fixed prices. Switch an existing merchant to native and rebuild to use visual trading.

Validation: **160 tests passed**, including native-store resources, finite quantities without NPC duplicates, guarded custom purchase paths, observed buybacks without fabricated prices, and offline native-store compilation. **43 native scripts compiled**. GUI interaction and actual transactions still need the user's in-game playtest; the agent has not launched NWN or Aurora.


Current build: `423fdeb423c5bb0a692b`. SHA256: `12418d637b7e5b0d132f56e2b36bbfdc535e82ca2b8e2e2934b85b36561834a9`.

## Previous trial: native visual companion inventory (0.9.2)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Visual Inventory Trial** (`rw_inventory.mod`). Old saves retain their previous inventory scripts. Existing modules remain intact.

Select a companion with `!companions`, then choose **Inventory - item grid** for a recruited party member or **Satchel - item grid** for a familiar/summon. Party members use NWN's native inventory. For a familiar/summon, your inventory opens: open its named satchel and drag item icons between the bag and your inventory. The satchel remains yours when the creature disappears. Use NWN's native item controls for examining and arranging items.

**Inventory - text list (fallback)** retains the working custom transfer panel. `!companion <alias> inventory` also opens the visual interface; append `inventory list` for the fallback. The AI inventory action uses the visual interface too. Opening through the suite still requires companion ownership and inventory permission; the native panel follows engine item rules. Pending custom handoffs must finish before opening it.

Merchant trading retains the existing purchase panel. This update covers companion storage. Physical room doors and previous AI companion features are included. Native GUI behavior and drag-and-drop still require the user's in-game playtest.


## Previous trial: physical room doorways (0.9.1)

Use **Play Adventure.cmd → New Adventure** for **The Silent Bell - Physical Doorway Trial** (`rw_doorways.mod`). Start a new game; older saves retain their old maps. All previous modules are preserved.

Interior corridor connections now have actual paired stock doorway tiles and native doors that open onto continuous walkable terrain. There are no corridor teleport signs or corridor transition zones. Outdoor connections remain trails; separate areas retain their area transitions. Studio's preview marks each physical doorway at its exported position. Door frames in compact rooms are placed to avoid overlapping, and furniture/actors keep clear of their entrances. Existing AI conversation, companion chest handoff and visual inventory features are included.

Validation: **154 tests passed**, **43 native scripts compiled**, and real installed walkmesh triangles checked through every interior doorway in this compact trial. The checks also verify solid wall geometry beside the openings. This is not an in-game playtest: please test walking through the doors with companions, including the vault's adjacent exits.


Current build: `b371b19c8b6afe407b65`. SHA256: `661ae56d2b996ecc37ed7f7089d65c12ebb5e65153712067356a607e4a109536`. Native resource counts: abbey 3 doors/1 area transition; road 0 doors/2 transitions; vault 5 doors/1 transition. Six doors connect interior rooms; two support area exits.

## Previous trial: companion and passage update (0.9)

Start a **new game** in **The Silent Bell - Companion and Passage Trial** (`rw_companion.mod`) through `Play Adventure.cmd`. Exit NWN and restart an older AI Player first; this trial requires AI Player 0.9.0. Old saves keep their embedded dialogue and area resources.

- Familiar/summon native dialogue now offers **Talk freely with AI**, companion controls, visual inventory and the original companion dialogue. After choosing chat and closing dialogue, speak normally in Talk. `!end` finishes the conversation.
- Chest inspection reads actual contents after the companion reaches an unlocked, untrapped, permitted container. It no longer waits for a player container window. It does not advance treasure quests.
- Ask naturally to take or deposit an item. Stand within three metres of the chest for direct handoff. Only one unambiguous, identified, transferable whole item/stack is moved; equipped, protected, cursed, high-value and container items remain excluded. Ask for the whole stack when necessary. No item is cloned or held by an expiring summon. Ownership is checked before a success report.
- **Open visual inventory** uses NWN's native grid for party members. For familiars/summons, open the named companion satchel in your own inventory to drag items. The custom inventory panel remains available. Merchant purchasing still uses its existing panel.
- All connection endpoints now have actual exit zones; supported solid interior boundaries also have stock framed native doors. Corridor terrain remains present. Quest conditions still apply. Followers travel; companions ordered to stay remain behind.
- Under **Encounters → Curated room design**, select a room and a design, preview, then apply. This replaces only that room's decorative furnishings. Story objects and NPCs remain. Presets use sparse purposeful groups; Aurora remains the final visual editor.
- Character replies receive in-world instructions and a filter for common software/game self-references, including the reported failure text. This reduces immersion breaks; it is not a guarantee against every possible generated phrase.

Please test: native familiar/summon dialogue, free chat, chest inspection and reported contents, one-item take/put and stack clarification, native inventory drag/drop, every room connection in both directions, followers, and the revised furniture arrangements. **NWN/Aurora gameplay has not been run by the agent.**


Current automated evidence: **152 tests passed**, including native script compilation and resource/link checks. **43 native scripts compiled** in build `f2568b029e8efe244337`. Four live AI checks passed: take, put, inspect-without-taking and old technical failure history. These do not prove in-game pathfinding or native GUI behavior.

Module SHA256: `d9b84edecce4e4a0f955b913909f4d1cf16ed8d961cc19c54d2954a11d58f634`.

## Previous trial: natural companion tasks (0.8)

Use **Play Adventure.cmd**, choose **New Adventure**, and select a character for **The Silent Bell - Natural Companion Trial** (`rw_natural.mod`). Older modules and saved games keep their embedded scripts; do not use an older save to test this update. AI Player 0.8.0+ is required. Existing modules, Aurora copies and saves are preserved.

Select a companion in `!companions`, choose **Talk freely with AI**, close the panel, then speak normally. Examples:
- "Go ask the merchant what swords he has for sale."
- "Could you look inside that chest and come back and tell me what you find?"

The AI selects one game-offered nearby object and an inspection or visit; the game rechecks exact object identity, ownership, creator/player permissions, speech mode, control, visibility and task availability. Ambiguous targets should prompt a question. A native **task started** receipt confirms dispatch. The companion must actually approach/open/ask and return before a report is confirmed. Contents are not read until the container is open. Locked, trapped or quest-gated containers remain unavailable. No purchase, theft, cross-area travel or quest advancement is added. Animals may inspect nonverbally but cannot conduct verbal visits. Precise commands and the task-selection menu still work without interpretation; natural interpretation requires live AI.

The old chest check incorrectly used GetObjectSeen, which the installed nwscript.nss documents as creature-only. Containers now use proximity and geometric line of sight plus the existing container/lock/trap/quest checks. Nearby observations include container names without exposing their contents.

Merchant controls use 550px content widths, companion controls 580px, and each inventory's contents 230px within separate scrolling panes. Width is applied to individual controls and group viewports only; enclosing row/column dimensions remain unconstrained. This replaces the 150px default widths seen in the screenshots while avoiding equal required parent/child dimensions. Rendering at the player's UI scale remains an in-game acceptance check.

Validation: 146 regression checks passed, including native compilation; five live AI checks passed for merchant phrasing, chest phrasing, negation, quoted speech and ambiguous containers. These language checks use a synthetic nearby scene and do not establish actual movement or GUI appearance. No NWN/Aurora launch performed by the agent.

Current native build: 35c43a718d19c46364b2; SHA-256 72c3015df03c1e48233a166ad5ada4ec0e94001115e93b269b42564b579bae07; 38 compiled scripts.

## Earlier release notes and reference


## Launcher working-directory fix (0.7.3)

The launcher previously started nwmain.exe with the installation root as its working directory. NWN requires the binary directory (`bin/win32`). The reported 3221225477 / 0xC0000005 crash had zero entries in all three installed base-resource keytables, missing PriorityGroups.2da and failed shader/UI resources during initialization, consistent with that path error. The launcher now starts from the binary directory for both New Adventure and Load Saved Game; CheckOnly displays that directory. Errors show the hexadecimal code and actual log location instead of assuming Steam/installation damage.

Source: [Beamdog developer guidance](https://forums.beamdog.com/discussion/67102/instanced-self-contained-installations/p1?new=1).

Run Play Adventure.cmd again. No module rebuild, game reinstall, key change or saved-game conversion is needed for this launcher-only correction. Current test module remains rw_uifix.mod. All 22 launcher tests passed, including new/saved working-directory checks and signed/unsigned access-violation errors. Game processes were simulated; actual launch remains the user's acceptance test. No NWN or Aurora launch was performed by the agent.


## Window sizing correction (0.7.2)

The reported error from rw_errands.mod was: "Error constructing window from json. The constraint cannot be satisfied". This is a layout-constraint failure, not evidence of missing JSON window fields. The previous 0.7.1 field additions alone did not address that sizing conflict.

Removed equal required widths/heights on both enclosing rows and their leaf controls. Rows/columns now size flexibly, controls retain readable heights, and each inventory column has an independent scrolling viewport. Removed the inventory row's fixed 740-pixel height and fixed column widths. Native UI rendering remains for user acceptance; regression checks cannot execute NWN's layout solver.

Use **Play Adventure.cmd** and choose **New Adventure** to load **rw_uifix.mod / The Silent Bell - Window Fix**. This was installed separately because NWN was running. Existing modules (including rw_playfix.mod and rw_errands.mod), saves and the running game are unchanged. Old saves retain their old embedded layouts.


- All 135 regression tests passed, including native compilation. The installed trial passed launcher readiness/context registration with AI Player 0.7.1; no API request or game launch. Eleven existing module files remained byte-identical.

- Targeted checks: bridge mailbox punctuation conversion without action/ID changes; social/visit display text; furniture footprint and actor clearance; chair/table grouping and orientation; non-mutating scale/repetition review; design-time guidance; merchant visit quotes from native observations rather than generated prices.
- Compiled module checks: every declared connection has usable native passage objects with valid arrival waypoints; corridor routes contain adjoining full-floor stock tiles; window JSON key contract matches the installed official nw_inc_nui constructor.
- Native compile and resource checks do not prove GUI rendering, navigation or actual actor behavior. These remain user playtests. The exact sizing error is now documented above; the 0.7.1 key-contract check alone was insufficient.
- New module rw_playfix.mod, build dd3e74dadedbcc925100, SHA-256 fda276592c2d71fc6d4c42e6c0d12ec5ff5aace7d41edb878993d31e65ffb664; 168 resources and 38 compiled scripts. Existing modules and saves preserved.
- No live OpenAI request, NWN launch or Aurora launch performed for this release.

## Historical validation

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


Current corrected native build: cb9f5d07b37c8e7f880e; SHA-256 623348ded87a82f81f448b7a625c7832e9a778a1864ca280d949f25551e5cfd7.

Installed window-fix trial: 8002076772c5d7e2bea3; SHA-256 18772a8b7a3ab361a5654e9828129094769a81ac677e70730f5bde3db3cb634d. All 135 tests passed; 12 existing modules remained unchanged.
