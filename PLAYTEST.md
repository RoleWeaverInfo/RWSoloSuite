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

