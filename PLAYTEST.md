# Module Studio 0.3 playtest — AI conversations, quests and merchants

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

