# AI NPC scope and server add-on port

Requirements confirmed on 2026-11-13. Source audit: RoleWeaverInfo/roleweaver-server, commit d64e3a1, clean local checkout. This is an implementation plan and capability audit, not a statement that every feature below is already in Solo Suite.

## Required experience

The module creator supplies a storyline and character details. AI NPCs deliver that story during play, while ordinary NPC menu dialogue remains an equally complete way to play. Both paths use one native quest state, journal, objective graph, reward ledger and set of endings. Players can switch between them at any point.

Every generated creature must be eligible for an AI profile, including monsters and incidental characters. Intelligent creatures use spoken dialogue; animals default to nonverbal behavior such as posture, movement, sounds and reactions. Creators retain per-creature AI controls, per profile and encounter template. Disabling conversation does not disable ordinary movement, combat or authored behavior. Encounter templates supply starting personalities; each spawned instance needs its own identity and history.

Companion integration covers both recruitable party members and existing familiars/summons. Party companions need recruitment, dismissal, relationships, owner/party authority and persistent identity integrated with the game's existing party controls. Familiars and summons need their own ownership, possession, resummoning and expiry handling. The server's existing familiar adapter does not yet cover recruitable party members or arbitrary summons; both need additional native adapters.

The live AI runs in a local player companion, with configurable provider credentials on the player's computer. No PW server is required. The module contains native conversations, stores, combat, movement, quest logic and its authored AI profiles. Online AI requires the companion and provider access; the native module remains playable when they are unavailable. Creating an AI-authored module and running live AI during play are separate operations.

## What is implemented in this branch

The first dependency is shared story progression. The AI now receives exact eligible actions for its current NPC and quest state: start a quest offered by that NPC, complete a current talk objective, or choose an authored branch. Unknown actions and actions belonging to other NPCs are discarded. A branch requires clear player intent; ambiguous discussion should produce a question instead.

Native NWScript rechecks the NPC, proximity, line of sight, combat, possession and exact objective state before applying the selected action. It calls the same AQStart/AQAdvance functions as menu dialogue, so journal updates, prerequisites, endings and one-time rewards are shared. Late replies cannot apply an earlier choice after menu progress changes. The transport already rejects stale sessions, changed focus and expired replies. This still needs the user's in-game playtest; compilation alone is not engine verification.

Implemented source: rwstudio/story_actions.py, rwstudio/authoring_ai.py and rwstudio/adventure_builder.py. Tests: tests/test_story_actions.py plus the optional-AI native exporter test. Version 0.3 also implements natural follow-up Talk, unambiguous full-name/alias addressing, explicit end/cancellation, and native merchant stock, exact prices, haggling and confirmed purchases through either menu or AI. See rwstudio/merchants.py, rwstudio/runtime_ai.py, authoring_scripts/aw_merchant.nss and tests/test_merchants.py. In-game merchant and quest verification is pending. The remaining capabilities below are still planned.

## Feature map

| Capability | Upstream evidence | Solo implementation required |
|---|---|---|
| Character voice, knowledge and secrets | conversation.py, knowledge.py, lore_documents.py; docs/LORE.md | Retain scoped profiles; add long-term curated memories tied to the save timeline and creature instance. Existing Solo profiles and bounded chat history are only the starting point. |
| Natural conversation and focus | docs/CONVERSATIONS.md, conversation.py | Name/address routing, follow-up Talk, explicit end, ambiguity handling, range and timeout controls; preserve native Talk To menus. |
| Every creature as an AI actor | No complete upstream monster adapter | Bind placed and spawned creatures by stable profile plus native instance UUID. Never resolve a pack of monsters through the first shared creature tag. Author controls conversation and language/voice per template. |
| Familiars | companions.py, companion_templates.py, companion_preferences.py; docs/COMPANIONS.md | Port personality templates, ownership, follow/stay, preferences, inventory recovery and saved identity. Attach to the actual summoned familiar rather than a replacement. |
| Recruitable party companions | Additional Solo adapter required | Integrate recruitment/dismissal, relationships, persistent identity, player orders and party authority with existing native party controls. Keep companion dialogue and memory scoped to the correct character and save. |
| Summons | Upstream familiar documentation explicitly excludes generic spell summons | Add separate discovery, ownership and dismissal/expiry handling. No commands or replies may reach a later summon through an old object reference. |
| Companion awareness and errands | companion_hearing.py, companion_inventory.py, companion_visits.py | Optional public listening, bounded inventory tasks, visits, reporting back and cancellation. Preserve the game's combat/order scripts and owner-only control. |
| Merchants | merchants.py, merchant_admin.py; docs/MERCHANTS_AND_LEADING.md | Implemented in 0.3 for eight stock goods, finite quantities, exact prices, chat/menu access, game-rolled haggling and native purchase receipts. Uses a native NUI goods panel; no buyback or restocking. In-game acceptance remains pending. |
| Inventory and barter | inventory.py; docs/INVENTORY_TASKS.md | Real item ownership, inspect/take/deposit/give/fetch/help, permitted chests, explicitly confirmed gifts/barter, plot-item protection and native inventory presentation. Adapt NWNX-dependent inspection to EE APIs and supported native UI. |
| Payments | interactions.py; docs/PAYMENTS_AND_NPC_COMBAT.md | Exact recipient, purpose, bounded amount and explicit player confirmation. Speech is never proof of payment. |
| Patrols | patrol.py; docs/PATROL_PREVIEW.md | Author-defined waypoints, route order, waits, loop/ping-pong policy, interruptions and pathfinding status. Patrol movement itself needs no LLM call. |
| NPC-to-NPC conversation | checkins.py, nearby.py; docs/NEARBY_BEHAVIOUR.md | Two-sided opt-in, travel to a visible recipient, short bounded exchange, pair cooldown, interrupt priority and game-confirmed speech. Private player transcripts do not become shared NPC knowledge. |
| Village routines | village.py; docs/VILLAGE_LIFE.md | Bounded home wandering, resting, approved seating, greetings and visits. Native routines run independently of model requests. |
| Perception | perception.py; docs/PERCEPTION.md | Observer-specific visible surroundings, injury and faction context, freshness and scan limits. Do not disclose hidden inventories, traps, quest locals or other NPC secrets. |
| Gestures and movement | actions.py, action_service.py; docs/CONTROLLED_ACTIONS.md | Exact authored action IDs, approved destinations, follow/lead/home, seating and usable unlocked doors. Native game validates and acknowledges effects. |
| Assistance and NPC combat | inventory.py, interactions.py; docs/PAYMENTS_AND_NPC_COMBAT.md | Use real healing resources; bound approved NPC aggression, pursuit and withdrawal. Native engine owns combat turns, rolls and damage. Monster AI is not an LLM call for each attack. |
| Encounter DM | dm_assistant.py, director.py, live_director.py, persistent_director.py | Port scene stages, actors, observations, outcomes, social checks and bounded direction against the compiled storyline. Keep generated quest mechanics and runtime scene state consistent. |
| Provider controls and language | provider.py, llm_settings.py, translation_service.py | OpenAI/local-provider adapters, request priorities, budgets, latency/error reporting and optional language support; do not copy server passwords or Redis configuration into exports. |

## Local architecture

1. **Authoring profiles and policies.** Version and migrate existing projects. Add creator-facing merchant stock, movement destinations, patrol routes, social permissions, companion templates and per-creature conversation controls. AI generation must produce the same editable policies as the manual editor.
2. **Native actor registry.** Use profile ID plus instance UUID, owner and lifecycle. Covers placed NPCs, each individual encounter spawn, recruitable party companions, familiars and temporary summons. Resolve actual objects again before applying commands. Keep independent actor histories even when blueprints/tags are shared.
3. **Native action layer.** Compile native stores and menus, common quest operations, patrol/idle scripts and permitted action handlers. Retain existing engine combat and summoning systems. Add menus for all substantive actions, not only a freeform-chat button.
4. **Local AI services.** Adapt the server's profiles, scoped memory, perception filters, merchant quotes, companion dialogue and bounded social orchestration to the existing local mailbox. Replace Redis/world-account conventions and NWNX dependencies with save-aware local equivalents; do not copy the Linux service stack wholesale.
5. **Save boundary.** The NWN save is authoritative for quests, actor identity, stock, items, rewards and confirmed outcomes. External memory must be keyed/reconciled to that save's timeline. Loading an older save must not retain later quest knowledge, transaction receipts or NPC gossip. In-flight work is cancelled on reload rather than replayed.
6. **Scheduling.** Player conversations take precedence over ambient chats. Combat, death, dismissal, possession and explicit orders interrupt background work. Only a bounded number of nearby actors are active; patrols, basic movement and combat run natively. Social visits have pair/global cooldowns and a configurable AI budget. An entire populated dungeon must not trigger one model request per creature heartbeat.

## Delivery order and acceptance

### 1. AI story and menu equivalence — implemented, awaiting playtest

Start a quest through AI, continue through menu dialogue, choose a branch through AI, finish its native interaction, and verify one reward. Repeat with the paths reversed. Change the objective while an AI reply is pending; its older action must be refused. Save/reload before and after the decision. Ordinary gameplay must still finish with the companion stopped.

### 2. Actor identity, conversation controls and save-aware memory

Generate multiple creatures from the same encounter blueprint. Address each separately, test unique histories, enable/disable conversation in the creator, and verify no replies after death/despawn. Reload an earlier save and check that future knowledge disappears. Natural-address routing must never choose arbitrarily between ambiguous actors.

### 3. Native merchants and companion adapters — merchants implemented in 0.3, companion adapters pending

Ship a merchant/companion test area. Buy via menu and chat, check finite stock and actual charged prices, test repeated haggles, cancel an exchange, recruit/dismiss a party companion, dismiss/resummon a familiar, expire a summon, cancel an errand, and recover inventory safely. Test party, familiar and summon authority independently, including existing party-control changes. Verify intelligent creatures speak and ordinary animals react nonverbally. No AI reply may invent payment, stock, delivery or ownership.

### 4. Patrols, social behavior and permitted actions

Ship an authored patrol and NPC social route. Verify physical movement, waits, one question/reply, cooldowns and memory attribution; interrupt through player conversation/combat. Test blocked routes, missing recipients and model outages without request floods or teleporting actors through walls.

### 5. Inventory, assistance, encounter DM and remaining parity

Add the remaining native/UI adapters and scene controls, then test the complete suite in a small playable adventure. Mark each matrix row implemented only after its source, native compilation, transport tests and user playtest are complete. Provider and translation options must state their actual supported scope.

## Compatibility limits

The existing server has capabilities implemented with NWNX_Item/Player and server-specific persistence/UI. Those integrations need EE-local replacements and cannot be promised as direct file copies. The installed EE header does expose native stores, associates, movement, speech, possession checks and object UUIDs, providing foundations for the local adapters. Exact native shop pricing, inventory exchange, summon handling and event timing still require implementation and in-game verification.

The current server add-on also does not provide unrestricted autonomous planning, an economy simulation, arbitrary spell-summon AI or automatic quest-variable changes. The Solo requirements extend that product in these areas; the port should preserve actual supported behavior rather than claiming those features already exist upstream.
