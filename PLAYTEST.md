# The Emberseal of Briarwatch — playtest checklist

The only bundled example is **The Emberseal of Briarwatch**, module `rw_ember_v3.mod`, project `emberseal_demo`. Use the build included with Studio 0.21.0-rc3 and start a new game. Old saves and older trial modules do not test this revision. See [the example guide](docs/EMBERSEAL.md).

1. On a fresh workspace, confirm only Emberseal is loaded. On an existing workspace, use **Load Emberseal example** and confirm any previous Emberseal draft is backed up.
2. Set the NWN folders and provider key. In **Build & share**, download the Share/Aurora ZIP and use **Play in NWN**. Confirm the module and its generated HAK install and character selection opens.
3. Use a level 3–4 character and the intended two-member party. Speak with Queen Elowen to start the missing-ward quest. Compare free AI speech and native quest dialogue.
4. Check the keep's indoor enclosure, throne/dais/carpet, guard and assistant rooms, and working doorways. Compare its uploaded floorplan with the visual editor and Aurora.
5. Walk through the walled stone courtyard, four merchant stalls and front gate onto the farm/forest road. Check that walls cannot be bypassed and passage endpoints are sensible.
6. Trade with Mara, Bram, Tavin and Alia. Recruit Hale if desired. Summon a familiar or creature through normal character abilities; use `!companions` and free AI conversation.
7. Ask a speaking companion to question a merchant and report back. Inspect an accessible chest, take one healing potion, then transfer it through the visual inventory. Check quantities and protected items. Animals should remain nonverbal.
8. Complete the three outdoor encounters and cave lookout encounter. Check Ember Hollow's enclosure and doorways. Defeat Skarn, take the Emberseal from his strongbox and return to the queen. Confirm the journal finishes and 300 gold is awarded once.
9. Pause/stop the AI service and use `!studio`. Check the disconnected/paused message and later reconnection, without blocking native quests or inventory.
10. In Aurora on Windows, with the HAK installed, open all three areas and save a separate copy. Verify the ZIP contains one adventure module and the matching profile, HAK, native resource sources and geometry sources.

Record the Studio version, build ID, platform and result for each check. Automated compilation does not replace these gameplay and visual checks. Do not include API keys in reports.