# First AI Edition playtest

The new AI module has been compiled and structurally checked, but it has not been opened in Aurora or played by the implementation agent. Your earlier successful Aurora check covered the original module, not this new AI Edition.

## 1. Aurora round trip

- Open `C:\Users\User\Documents\Neverwinter Nights\modules\mc_courier_ai.mod`.
- Confirm **Wayfarer's Hall** and **Hollowstone Cave** open, with Edric, Mara, Tavin, the quest cache and the three placed enemies.
- Confirm the optional **Returning scavengers** waypoint exists in the cave. Its creatures should not exist yet.
- Open Edric's conversation and find **Talk freely with AI** alongside the authored quest options.
- Save As `mc_ai_aurora.mod`. Keep the generated original available for the first game test.

## 2. Local connection and NPC conversation

- Open Solo Studio at `http://127.0.0.1:8766`, choose **AI DM Assistant**, and start the companion if paused.
- Start a fresh single-player game in **The Missing Courier — AI Edition**, preferably with a level 1–3 character/party.
- Verify Studio shows a live character, area and party. If it is waiting, resume the game for 6–12 seconds. Settings must point to the same NWN user folder the game uses.
- Speak to Edric, choose **Talk freely with AI**, close the dialogue, and type `!ai What happened to the courier?` in chat.
- Confirm a reply appears in the game. Try `!talk mara How can I prepare?` while near Mara.
- Walk away while a request is pending. The late reply should not grant quest progress or continue a remote NPC conversation.
- Test the game's existing party-control options. The live snapshot should include nearby faction/party members; report any controlled member whose chat is not received or whose stats are missing.

If chat does not work, report whether Studio ever showed a connected session, the exact command used, the in-game message, and whether the game was paused. A screenshot of the DM panel and chat log is useful; do not include API credentials.

## 3. Complete the quest

- Accept through the authored dialogue first. Verify the journal entry and three healing potions.
- Enter the cave, fight the placed enemies, speak to Tavin, and recover the satchel from the cache.
- Return to Edric. Try `!talk edric I have your satchel and would like to hand it over.`
- If the model only talks instead of requesting turn-in, the authored **Here is the recovered item** choice must still finish the quest.
- Confirm the item is removed, the journal completes, and 150 gold / 300 XP are awarded once.
- Ask again, reopen the conversation, save and reload. Confirm the reward cannot be repeated.
- On a separate fresh run, try accepting through AI, and recovering the item before accepting the quest.

## 4. DM and encounter review

- In the cave, type `!dm Is this party ready for another small encounter?`.
- Check that any encounter suggestion remains a proposal until you choose **Deploy encounter** in Studio.
- Heal, finish combat, and stand at least six metres from the Returning scavengers marker. Deploy it and resume the game.
- Look for an acknowledgement stating the number of creatures created. Retrying should be rejected because the encounter is spent.
- Try **Remove its creatures**. Authored enemies, quest characters and furnishings must remain.
- Save/reload and verify that the encounter's spent state is preserved.
- If using a larger party, compare the acknowledged creature count with the base/maximum and the documented scaling rule.

## 5. Failure and save behavior

- Pause the companion and continue the quest through ordinary dialogues. It must remain completable.
- Submit an AI request with the companion paused; the game should eventually give a timeout and remain playable.
- Save before a conversation, exchange a few lines, then reload. The NPC should not remember conversation text from after that save.
- Reload during a pending request. A response from the discarded session must not apply to the reloaded game.
- Make sure new game requests work again after the companion is resumed.

## 6. Authoring smoke test

- Create a separate new project or import a copy; keep the sample intact.
- Edit a character's voice, rename an area, and change an encounter.
- Ask the authoring assistant to add an optional cave, one support NPC, furnishings and a stock rat encounter. Review the draft before applying it.
- Build, install, open in Aurora and start a new game. Verify new travel signs work both ways and party members travel with the player.
- Report blocked placements, inaccessible signs, incorrect creature behavior, missing dialogue, compile errors, or AI lore that disagrees with the authored world.
