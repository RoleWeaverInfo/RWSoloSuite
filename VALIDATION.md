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

