# Module Studio 0.7 — one launcher for game and AI

Use **Play Adventure.cmd** in the RWSoloSuite folder, or extract the complete `rw_errands-aurora.zip` and use its module-specific launcher. The existing `rw_errands.mod` and your saves are unchanged; no new game is required just for this launcher.

1. Save/quit NWN for the first clean launch test. Stop any manually started AI Player if you want to test cold startup. Double-click **Play Adventure.cmd**, choose **1**, and confirm AI becomes ready before NWN opens at the normal character-selection screen for the correct module. Choose your character, unpause and ask an AI NPC a question.
2. Keep the launcher window open during play. After NWN exits, a worker started by this launcher should stop. A previously running AI Player should remain running. Do not close another authoring session merely to test this.
3. Launch again and choose **2**. At the game menu, use Load Game and select your existing trial save. AI should work without separately starting/importing anything. `Play Adventure.cmd -Resume` is the equivalent direct option.
4. With NWN already running, run the launcher: it should enable/reuse AI but never close the active game, open a duplicate game, replace a differing module file or discard an unsaved session. Switch back and use the currently loaded module/save.
5. In a separate test environment, stop only the launcher-owned AI worker while playing. The launcher should restart it, register the same context and tell you to repeat any interrupted question. Repeated startup failure should be reported; the game must not be killed.
6. Run `Play Adventure.cmd -Offline` to play without live AI. Native quests, merchants and companion controls should work; an existing bridge should be paused. Missing keys, mismatched sidecars, missing Python, game path errors or an incompatible older AI Player should produce an actionable error rather than an apparently ready AI game.
7. Extract the complete adventure ZIP into a folder with spaces and run its launcher. It must include the **AI Player** folder and matching .rwproject.json, install/backup the module as needed, and keep game, sidecar and context matched. Do not distribute just the .cmd or a developer's data/settings folder.

126 automated checks cover the launcher plus existing features. The real PowerShell/Python entry point is checked with `-CheckOnly`; game process launch/lifecycle tests use fake processes. The game CLI options were verified in the installed official NWN:EE v74 release notes (Patch 1.66): +LoadNewModule selects the module and opens character selection, while +TestNewModule auto-selects a character and is deliberately not used. Actual Windows/Steam handoff and in-game AI still require your test. No NWN or Aurora instance was launched by the agent.

---

# Module Studio 0.6 — companion inspection and visit tasks

Start a **new game** with **The Silent Bell — Companion Errand Trial** (`rw_errands.mod`, installed separately). Keep **Start AI Player.cmd** running for NPC visits. Older modules and saves are unchanged.

1. Recruit **Seren Ashford** in the guest hall. Use `!companions`, select Seren and scroll to the task controls. Choose **Inspect a nearby container**, then select the guest-hall **Healing supplies cache**. Do not loot it first: the test needs contents to inspect. Watch Seren walk to it, interact, return and report the actual contents without taking anything.
2. Also try `!companion seren inspect Healing supplies cache`. After a completed report, ask Seren through ordinary AI what was found. Compare against the real container. Empty it yourself and inspect again: the new report should say empty, without assuming its previous contents remain.
3. Set up locked/trapped and quest-gated containers in a separate Aurora copy. Inspection must refuse inaccessible targets or fail when the native interaction cannot open them, with no reported hidden contents, loot, trap bypass or quest reward. Test multiple similar chests: ambiguous generic names must require an exact target.
4. Use `!companion seren ask ilyra Where is Rowan?`. Watch Seren approach Ilyra, speak the question, wait for Ilyra's actual answer, return and report it. The report must not arrive while Seren is still away. The journal/reward state must remain unchanged by this visit.
5. Try the **Visit an AI NPC and report back** target picker. It asks “How can you help us?” by default; chat commands allow a specific question. Target recipients must have **Accept owner-directed companion visits** and AI enabled. Ordinary ambient social settings are independent.
6. Repeat with a normally summoned speaking familiar (e.g. imp/pixie) and an intelligent summon, using `!companion familiar ask ilyra Where is Rowan?` or `!companion summon1 ask ilyra Where is Rowan?`. Use a cat/bat for inspection: expect nonverbal behavior and the owner's factual observation receipt, not invented animal speech. A nonverbal companion must not launch a verbal NPC visit.
7. While travelling/waiting, use `!companion seren status`, then `!companion seren cancel`. Also use a newer native Follow/Stand ground order, possess/control the creature, enter combat, change its preferences, change area, dismiss a familiar or expire a summon. Tasks should stop; newer native orders must survive cleanup. A disappeared actor must release the recipient's visit lock.
8. Talk to Ilyra yourself while the companion's answer is pending. No stale answer/report should arrive after that interruption. Try a dead, busy, recruited, distant, unseen or non-opted-in recipient, a blocked route and a paused game beyond the visit timeout. No repeated API calls, teleport or fabricated success.
9. After a successful return, verify the previous native follow/stay/guard mode resumes. For an interruption during combat, cleanup must not clear the combat queue. Try another task after cleanup; stale task modes must not become the new default.
10. Disable inspection/visits for the source template or recruit in Studio, and disable **Accept owner-directed companion visits** on a recipient. Rebuild a different module name and start a new game: disabled tasks/targets must not run. Turning player movement/AI preferences off must also restrict the relevant task. AI-disabled exports should keep inspection but contain no visit mailbox scripts.
11. Save before a task, while travelling, while awaiting an answer, and after an answer but before return. Reload each save. Check native task state and reports match that save, late responses are rejected and no future knowledge appears. Repeat familiar death/resummoning and summon expiry while a task is active.
12. Open `rw_errands.mod` in Aurora, inspect source/recipient profiles, new native task scripts and ordinary quest resources, and Save As a separate copy. Native chest opening, associate movement and reporting timing are still engine acceptance checks, not proved by compilation.

105 automated checks pass, plus one real recipient-answer model check using synthetic identities. No NWN/Aurora instance was launched by the agent. This is a same-area, visible-target task foundation: no fetching, locks/trap work, cross-area visits or companion-driven quest changes. Existing speech, inventory, merchant, patrol and quest regression instructions follow.

---

# Module Studio 0.5.1 — NPC speech and native panel fixes

Start a **new game** with **The Silent Bell — UI & Speech Fix** (`rw_ui_fix.mod`, installed separately). Keep AI Player running. Your previous modules/saves are unchanged and do not receive these scripts automatically.

1. Speak to Ilyra or Seren through AI. Successful replies should now appear as ordinary speech from the NPC, with the usual in-world speech display and Talk chat text. They should not be duplicated as yellow system messages. Connection errors, DM hints and control receipts still use system text.
2. Open `!companions`, select an actor and scroll the window. Check that all settings, **Talk freely with AI** and **Back** are accessible. Resize the window if useful and check your normal GUI scale.
3. Recruit Seren and open inventory. Expect two visible columns: **YOUR BELONGINGS - give** and **COMPANION STORAGE - take**. Equipped, protected, unidentified, cursed and other restricted items should be listed with disabled buttons and a reason. No transfer occurs merely by viewing.
4. Collect the guest-hall healing supplies to obtain a loose eligible item. Scroll the inventories, use each side's Previous/Next controls, give one whole potion stack to Seren, reopen/refresh and take it back. Check actual inventories and confirmation, including merged stacks. Nothing should be copied or recreated.
5. Summon normally and open its inventory. Its recoverable owner-held satchel starts empty; the left column must still show your belongings. Give an eligible item, dismiss/expire the summon and recover that same item from the bag. The satchel is not a view of the creature's innate equipped weapons.
6. Open Bram's shop. Scroll through all five authored stock lines and the Refresh/Haggle/Close footer. Test purchase and haggling without hidden rows. This shop lists authored sale stock, not every piece of NPC equipment.
7. Repeat at your normal window resolution/GUI scale and report anything still clipped. Check both the scrollbar and window resizing. Re-test older quest, companion and patrol/social behavior using the procedures below.

Native scripts compile and 92 automated checks pass. These changes have not been run in NWN/Aurora by the agent; actual speech bubbles, scrollbar rendering, widths and transfer behavior need your playtest.

---

# Module Studio 0.5 playtest — patrols and NPC social chat

Start a **new single-player game** with **The Silent Bell — Patrol & Social Trial** (`rw_ambient.mod`, installed separately). Older saves do not acquire the scripts. The original courier, merchant and companion trials remain unchanged. No NWN or Aurora instance was launched during development.

1. Run **Start AI Player.cmd**. Studio 0.5's development instance is already enabled. Start in the abbey guest hall and keep the game unpaused.
2. Watch **Mira Fen** and **Tomas Reed** walk to the guest-hall stop, wait and patrol to the sanctuary and back. Mira waits 30 active seconds, Tomas 45. They should walk through the actual corridor, never teleport. Stand near their shared stop to observe a two-sided public exchange. Each line should come from the correct NPC, with a short gap.
3. Talk to either NPC through their ordinary menu while walking or awaiting an ambient response. Movement/social speech should yield. Send a freeform player question while a social response is pending: player work takes priority; an interrupted exchange must not resume later as stale dialogue. Existing quest and merchant menus must still work.
4. Separate the NPCs beyond six metres, break line of sight, enter combat, kill/raise a mortal test actor, possess an actor or recruit an eligible test NPC. No delayed social line should arrive for an unavailable or changed actor. Use normal companion controls to check recruitment still stops ambient behavior and does not replace native follow/combat.
5. Stay nearby for several minutes. Exchanges must respect global and per-character cooldowns, and the six-attempt budget per active hour. Failed/interrupted attempts count too. No NPC should submit AI calls every heartbeat. After an attempted request, pause for over 90 wall-clock seconds, then resume: the old social exchange should be discarded.
6. Save before public speech, continue and save again, then reload the earlier save. The later public conversation must not appear in that earlier timeline. Test reload while the first line is pending and between first/second lines: no duplicated or late reply. Recruited companion handlers must still work after reload, without recursive event errors.
7. In Studio's **Behaviors** page, disable social globally, rebuild with a different module filename, start a new game and verify patrols still run but NPC-to-NPC calls stop. Then disable only one partner's social flag, or exclude the other from its partner list: the pair must not converse. Test a nonverbal social profile and ensure it does not speak quoted words.
8. Disable patrols globally and rebuild: both caretakers should remain at their authored placements. Enable globally but disable only Mira: Tomas should patrol while Mira stays. Reorder/add/remove stops and test both route modes and wait/run controls. Invalid rooms, other-area stops or routes without ordinary corridor access must fail the adventure check.
9. Disable live AI at export, leave patrols on and rebuild a distinct trial. With Studio closed, patrols and all ordinary quests, merchants and companion commands should still run. The editor warns that social AI cannot run in that export.
10. In a separate Aurora copy, block a route with solid geometry. The NPC should fail or time out, wait before retrying and never teleport or loop API requests. Also verify movement does not override a cutscene-controlled actor or native combat.
11. Open the final `rw_ambient.mod` in Aurora, inspect its three areas, Mira/Tomas, native routes/configuration, dialogues and source scripts, then Save As a separate copy. Aurora edits are not imported back into Studio.

These tests require actual game/Aurora verification. Automated compilation and resource assertions do not prove pathfinding, event timing, native speech rendering or save/reload behavior. This first adapter supports authored NPCs in one area, not social visits or arbitrary encounter spawns. Previous companion/quest/merchant regression steps follow.

---

# Module Studio 0.4 playtest — party, familiar and summon companions

The new trial is **The Silent Bell — Companion Trial**, filename **rw_companions.mod**, installed in your NWN user modules folder. It has 3 areas, 5 NPCs, 2 quests and the existing merchant. Start a **new game**; older saves do not acquire these scripts. No NWN or Aurora instance was launched during development.

1. Start **Start AI Player.cmd** (the development instance is already enabled), then start the Companion Trial locally. Seren Ashford, Ilyra and Bram are in the guest hall.
2. Speak to Seren. Check ordinary dialogue, **Companion controls** and **Join my party**. Alternatively type `!companions` near Seren. Recruit her; check native party membership and portrait. Dismiss and recruit again. Recruitment should not spawn a duplicate. Seren is essential in this trial.
3. Test Follow, Stand ground and Guard master from the controls, then issue a newer native party command. Check native combat still works. A waiting recruit should stay when you use a generated exit; following recruits should travel with you. Return for anyone left waiting.
4. Choose **Talk freely with AI**, close the controls, and speak normally in Talk. Try `!companion seren How can you help?`. Verify personality and recent conversation memory. Toggle AI off: no AI requests or late replies should arrive, while normal dialogue and party controls still work. Test brief/detailed replies and tone.
5. Use a character with a familiar ability and a summon spell. This trial does not grant them: prepare the normal class spells/abilities. Summon normally, then use `!companions` to select the exact body. Test `!companion familiar Hello` and `!companion summon1 Hello`. Cats/bats/ravens/hell hounds default to nonverbal reactions; imps/pixies/mephits/dragons/eyeball kin use speech. Generic summons use the creator profile and their observed intelligence/race.
6. Give the familiar a memorable harmless fact. Dismiss with its normal game control, resummon and ask about it. Its recent history should persist. Expire/dismiss a summon and create another: the new instance must not inherit the old summon's history or pending orders.
7. Send an AI movement request, then possess/control that actor, change native orders, dismiss it, enter combat, move away, or change its settings before the response returns. The old reply/action should be discarded. Unpossess and select again to continue. Original familiar death penalties and native summon expiry must still occur.
8. For inventory, use a spare unequipped mundane item or potion stack. Click Give/Take once and confirm exactly one whole object/stack moves. Check partial failures, merged stacks, full inventory, repeated clicks and equipped/plot/cursed items. The owner may stop their current queued movement when explicitly confirming a transfer. Do not retry an unconfirmed transfer until checking both inventories.
9. Open familiar/summon inventory to create its owner-held satchel. Put an eligible item in it. Dismiss/expire the creature; recover the same item through **Recover familiar / summon satchels** or normal inventory. No copied/replacement item should appear. Empty satchels may be discarded; nonempty ones must remain recoverable. Native bags are the recovery fallback if the Give/Take engine action cannot complete.
10. Save before recruitment/chat, continue and save again, then reload the earlier save. Party membership, history, settings, bags and quest state should match that save, without later memories. Test save/reload with a request/transfer pending, familiar death and re-creation, and a summon expiring.
11. In the editor, test recruitment gates, movement/inventory restrictions and disabled template AI. Rebuild under a distinct module name and start a new game. Owners must never expand creator permissions. AI-disabled builds should still offer native companion commands and authored quests with Studio closed.
12. Open `rw_companions.mod` in Aurora. Confirm Seren, native dialogues, 3 areas, satchel blueprint and companion scripts; Save As a separate copy. Aurora edits are not imported into the Studio project.

Fetch errands, NPC visits, relationship scores and AI spell/healing control are outside this release. Animal companions/domination are also outside these three adapters. Use the quest/merchant checks below on this trial as regression coverage.

---

## Previous quest and merchant regression procedure

The new trial is **The Silent Bell — AI & Merchant Trial**, filename **rw_ai_market.mod**. It has been compiled and installed in the local NWN user modules folder. It has not yet been played or opened in Aurora. Start a **new** game; older saves do not acquire the new scripts.

## Start

1. Run **Start AI Player.cmd** from the RWSoloSuite folder, or open http://127.0.0.1:8766/player and choose Start companion. The instance prepared during development is already enabled.
2. Start a new local single-player game with **The Silent Bell — AI & Merchant Trial**, ideally at level 1–3. The opening area is Emberwake Abbey. Ilyra and merchant Bram Ironstock are in the guest hall.
3. Keep the game unpaused while waiting for AI; native heartbeat delivery stops while the game is paused. The goods panel and ordinary quest menu do not need the companion.
4. For purchase tests, use available character gold, or earn 50 gold from the first quest and 100 from the final quest. Opening/closing the shop costs nothing; insufficient funds must not deliver an item.

## AI conversation and shared quest state

- Near Ilyra, use **Talk freely with AI**, close the dialogue, and ask a normal Talk question. Then ask a follow-up without repeating her name. Check that both replies arrive from Ilyra.
- Also try **!talk ilyra What happened to the bell?** or **Elder Ilyra: Hello**. Use **!end** to finish. A name address must be unambiguous. Unknown colon addresses end the old focus; OOC, party and tell text must not trigger replies.
- Ask Ilyra where Rowan is. Check that discussing the current talk objective advances the same journal used by the NPC menu. Talk to Rowan through the menu, defeat the wolves, and talk to Cael through AI or the menu. Verify the first quest pays only once.
- Solve the vault inscription with **Trust**, recover the clapper, then return to Ilyra. Save before the final decision.
- Through AI, clearly say **I have decided to keep the bell silent and seal the clapper in the archive**. Check the journal selects the sealing objective. Use the archive object to complete the story.
- Reload the pre-choice save and choose restoration through the NPC menu. Use the sanctuary bell stand. Verify this path completes, gives its own outcome and cannot pay repeatedly.
- At the branch decision, the native menu must still offer AI chat and ordinary topics. Quest-gated topics must remain locked until the specified quest completes.
- Send a talk/choice request, then progress through the menu before its response arrives. An older action must not rewind the quest or grant another reward. The native message may ask you to continue because the story changed.
- Pause the companion and finish through ordinary menu/object interactions. Repeat a completed conversation and reload a save: rewards should not repeat. Death/respawn, party travel and both endings still need engine verification.

## Merchant menu, AI and actual purchases

1. Approach Bram within six metres, visible and out of combat. Open his NPC menu and choose **Show me your goods**. Expect a native **Merchant goods** panel with gold balance, finite quantities and explicit Buy buttons.
2. Close it without buying. Your gold, inventory and his stock must be unchanged.
3. Use **!talk bram What do your daggers cost?**. The initial price is 2 gold unless a haggle offer applies. AI must quote actual observed stock/prices.
4. Use **!talk bram I would like to buy a dagger. Show me your goods.** Check the same panel opens. AI speech alone must not move gold or items.
5. Click Buy once. Check one dagger arrives, the exact displayed amount is deducted, stock decreases by one, and a **PURCHASE CONFIRMED** receipt appears.
6. Buy the last dagger, then try again. The row should be sold out; neither gold nor another dagger should move. A quick double click must not purchase the same stock object twice.
7. Check the potion cache in the hall. With potions already in your inventory, buy one potion from Bram. The existing stack must grow by exactly one, never shrink, and his stock must decrease by one. This merge behavior is a particularly important engine test.
8. Try insufficient gold, moving away, entering combat, and clicking a stale panel after save/reload. No unaffordable or stale purchase should succeed. Reopening should show fresh stock and prices.
9. Save after a purchase, reload it, and check stock/gold/items remain consistent. Load a save from before that purchase: all three should return to that older state together. Reloading while an AI response is pending must discard its later action.
10. Stop the AI companion and repeat a menu purchase. Native merchant interaction must continue to work.

## Haggling

- Through the menu or AI, ask Bram for a better price. Expect a game-rolled d100 result and a refreshed panel. Default chance is 50%, discount 5%, duration 600 active game seconds.
- Repeated requests during the period must reuse the result, including failures, and must not stack discounts.
- Check the charged price equals the panel. Prices round down to whole gold, minimum one; 5% off a 2-gold dagger therefore becomes 1 gold.
- Save/reload within the offer. Its result and remaining active-game duration should follow the save.
- After the offer expires, a panel showing an older price must refresh and require another Buy click rather than charging an unseen price. For a shorter test, make a separate project copy with a 60-second offer, rebuild, and start a fresh game.
- Disable haggling in a separate creator test: neither the NPC menu nor AI should offer that action.

## Creator and Aurora checks

- In **Characters**, choose Bram. Edit stock quantity, price and haggling rules, save, build and start a new game. Confirm the generated panel matches those edits.
- Turn off AI conversation for Bram and rebuild: the shop menu should remain. Disable the shop and rebuild: merchant menu/actions should disappear. An existing save retains its original authored configuration.
- Ask the authoring AI to add a merchant to a separate adventure. Review the proposed stock/prices and export it. The same limits and controls must apply to AI and manual edits.
- Open rw_ai_market.mod in Aurora. Check three areas, seven rooms, four NPCs, both quests, Bram's stock items and merchant menu scripts. Inspect the aw_merchant, aw_shop_evt, aw_ui and aw_story source resources. Save As rw_ai_market_aurora.mod and reopen.
- A shared module should still run its menu quests and merchant panel on another current Windows NWN:EE installation without Studio or a key. Optional AI needs that player's local companion and credentials.

Please report module/build, area, objective or item, action, gold/quantity before and after, visible message, and whether the game was paused. Screenshots are useful; do not include API credentials.

