# Module Studio 0.2 playtest

The new exporter has compiled the example adventures and checked their native resource structure. These builds have not yet been opened in Aurora or played. Your previous Aurora check covered the original Missing Courier module only.

## Aurora

1. Start Module Studio, select **The Silent Bell**, then **Build & share**. Build the current project and choose **Install for playtest**, or open the distributed rw_silent_bell.mod directly in Aurora.
2. Open all three areas and check seven rooms, furniture, three NPCs, wolves, caches, inscription and exit positions. The layout preview uses the same corridor plan as the exporter.
3. Inspect Ilyra's conversation for the final branching decision. Inspect the two journal categories and aw_* / aq* scripts.
4. Save As silent_bell_aurora.mod, reopen it and verify the resources survive. Keep the generated original for the first gameplay test.

## A complete local adventure

1. Start a new single-player game using The Silent Bell. Try a level 1–3 party first. Close Studio to confirm the ordinary adventure runs independently.
2. Read the opening and journal. Speak to Ilyra, travel to the road, talk to Rowan, defeat the wolves and return to Cael. Verify each objective progresses and the first quest pays once.
3. Travel to the vault. Solve the inscription with **Trust**, recover the clapper, then speak to Ilyra. If a new decision becomes active while talking, close and reopen the conversation.
4. Save before choosing the bell's fate. Choose restoration and use the bell stand in the sanctuary. Check the completion text, journal, rewards and ending.
5. Reload the pre-choice save, choose sealing and use the archive reliquary. Check that this branch completes and displays its own outcome.
6. Reuse completed objects, retalk to NPCs, save/reload and confirm rewards do not repeat. Test recovering the item and solving the puzzle before their objectives become active.

## Travel, encounters and party behavior

- Walk through marked exits and also try the clickable passage signs. Check both directions and that arrival does not bounce back. Check living party members travel with you.
- Walk each corridor and reach each NPC, cache and quest object. Report invisible barriers, blocked furnishings or inaccessible exits.
- Compare wolf numbers on separate fresh runs with different party sizes. Scaling is applied once when the area is entered, bounded by the encounter maximum; it is not continuous rebalance.
- Use your normal party-control options. Report missing journal/chat feedback or any controlled party member unable to interact. No party-control modifications were installed.
- Test death/respawn and saving in each area. This initial release still needs native engine timing and balance verification.

## AI-generated example and your own story

1. Select **The Starlight Trial**, build/install and play it. It was generated from a short story plus a two-room, 14×10-tile stone dungeon specification. Check its native quest journal, encounter and puzzle, then both decision outcomes on separate saves.
2. Create a new adventure. Write a short storyline, define an area and room count, generate a layout and connect its rooms. Add character knowledge and an encounter brief.
3. Ask the AI DM to generate a complete adventure. Review, apply and edit the proposal. Verify the requested area dimensions/type/room count remain intact, all rooms contain useful content, and the quest has an ending.
4. Check, build, open the module in Aurora and play the entire story. Copy the share ZIP to another NWN:EE installation and verify ordinary play without Studio or an API key.

## Optional live AI

1. Enable optional live conversations in Build & share and rebuild. Run **Start AI Player.cmd**, then start a fresh game with that build.
2. Choose **Talk freely with AI** on a nearby key NPC, close the conversation and use `!ai What can you tell me?`, or `!talk ilyra Why did the bell fall silent?`. Try `!dm Give me a spoiler-free hint`.
3. Keep the game unpaused. Verify replies, scoped knowledge, quest-gated secrets and context after a quest completes. Ordinary dialogue must remain sufficient to finish the adventure.
4. Pause the companion, walk away during a pending NPC request, and reload a save while a response is pending. Stale/remote replies should not apply. Resume the companion and confirm new requests work.

When reporting a problem, include project/build, area, current objective, action, visible result and whether the game was paused. Include a screenshot or save if helpful, but never API credentials.

