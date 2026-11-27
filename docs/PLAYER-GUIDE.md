# Playing with AI characters and companions

The included example is **The Emberseal of Briarwatch** (`rw_ember_v3.mod`). Fresh Studio installations already contain its project and build. Choose **Build & share → Play in NWN**, or use **Load Emberseal example** first on an existing installation. The [Emberseal guide](EMBERSEAL.md) covers the queen's quest, merchants, optional recruit and required HAK. No Silent Bell or other trial module is needed.

Start Role Weaver before NWN. Register the adventure's matching `.rwproject.json` and leave the AI service enabled. Use your own API key. [Installation and setup](INSTALLATION.md) explains these steps.

Newly rebuilt AI-enabled modules check the service when you enter. After a short startup grace period, an in-game system message tells you if Studio is not connected or its AI service is paused. It also reports when the connection returns. Type **`!studio`** in Talk to check at any time. Keep NWN unpaused while the check runs. Closing the dashboard's browser tab is fine; the service itself must stay running.

If the service stops during play, detection takes roughly 30 seconds plus a module heartbeat. Slow AI replies do not interrupt this connection check. “Connected” confirms the local service, not API credit, a working key or a registered adventure profile. Native dialogue, quest menus and inventory remain available. Old modules/saves do not acquire new scripts automatically: update Studio, rebuild the module and start a new game to use the check.

A native NWN module cannot directly launch the desktop service. Start Studio yourself before NWN (or switch out of NWN and start it when warned). No automatic operating-system startup setting is enabled by this feature.

## Talk to an AI NPC

1. Walk near the character and open their conversation.
2. Choose **Talk freely with AI**, close the dialogue menu, and type ordinary sentences in the game's **Talk** chat channel. For example: “Your Majesty, what happened to the missing seal?”
3. Leave the game unpaused while they answer. Type `!end` to end that conversation.

You can also address a nearby NPC directly with `!talk <alias> <message>`. For a character whose alias is `bram`, use `!talk bram what swords do you sell?`. `!ai <message>` sends a message to your selected AI conversation partner. Names/aliases depend on the adventure; Bram is only an example.

### Find a nearby character with `!npcs`

In modules converted or rebuilt with **Studio 1.3.0 or later**, **`!npcs`** opens a nearby-NPC list. It is useful when the original dialogue has no AI option or several characters share a name:

1. Finish any required quest choice and close the dialogue menu.
2. Type `!npcs` in the game's **Talk** channel with the game unpaused.
3. Select the character by name and distance. Type an ordinary question in Talk when the selection menu closes.
4. Type `!end` to finish. Open `!npcs` again to choose someone else, or use its refresh control after moving.

Characters must have AI enabled, be visible within 12 metres, and be available outside combat, cutscenes and active dialogue. The list does not bypass quest restrictions or a creator's AI opt-out. Use `!companions` for familiars and summons. This list is currently specific to converted modules; Studio-created adventures such as Emberseal use **Talk freely with AI** or `!talk <alias> <message>` instead.

The normal dialogue menu remains available for quest choices and other authored actions. AI conversation availability, creature speech/nonverbal behavior and what each character knows are controlled by the module creator. An AI promise alone does not complete a quest or transfer an item: check the journal, inventory and game's actual result.

### Adjust AI replies while playing

In adventures built or rebuilt with **Studio 1.3.0 or later**, including the refreshed Emberseal example, type **`!aisettings`** in Talk to open **AI response settings**. Close the current dialogue first and leave the game unpaused. Converted adventures also offer this button in `!npcs`, and companion controls include it too. Click each setting to cycle its options:

- **Reply length:** Brief, Normal or Detailed. Normal is the default: 2–4 short sentences, up to 90 words and 600 characters.
- **Speaking style:** Plain, Characterful or Dramatic. Characterful is the default; vocabulary and manner reflect the NPC's profile.
- **Action descriptions:** Off, Occasional or Expressive. Occasional is the default: at most one short gesture when useful. Animals still communicate through physical behavior.
- **Follow-up questions:** Only when needed, or Conversational. Conversational is the default: a relevant follow-up is allowed when it fits the character, without requiring a question in every reply.

Changes apply to new requests and persist when you save the game. A reply already being generated keeps its earlier settings. **Restore defaults** selects Normal, Characterful, Occasional and Conversational. The settings affect NPCs, merchants and companion dialogue, including replies to companion visits; they do not change quests, permissions, the AI DM's narration or ambient NPC exchanges.

New companions inherit these settings. To override one companion's length, use its **Reply** control under `!companions`; choose **Use AI response settings** to return to the shared default. Existing explicit companion preferences are retained. Companion tone remains a separate per-character choice.

The service encourages natural speech in existing adventures too. Adding the in-game panel or updated defaults to an older module requires rebuilding and starting a new game; an old save keeps its embedded scripts and preferences. For an existing game with `!aisettings`, select the four choices manually (older panels call Normal length **Natural**). No additional API request is made when you change a setting.

### Quick command reference

Enter these commands in **Talk**, with NWN unpaused and the dialogue menu closed. Keep Studio running and the matching adventure profile registered.

| Command | Use |
| --- | --- |
| `!npcs` | Choose an available nearby AI NPC in modules converted with 1.3.0 or later |
| `!aisettings` | Adjust future AI replies in adventures built or rebuilt with 1.3.0 or later |
| `!companions` | Select and control recruited party companions, familiars and summons |
| `!talk bram what swords do you sell?` | Address a nearby NPC by its adventure-specific alias; Bram is an Emberseal example |
| `!ai Tell me more.` | Speak to your selected AI conversation partner |
| `!end` | End the current AI conversation |
| `!studio` | Check the connection to the local service without an AI request |
| `!missions <name or alias>` | Open available Studio-controlled mission actions in supported converted adventures |

If a new command is unavailable, verify the module was rebuilt with 1.3.0 and start a new game. Updating the service alone does not replace scripts inside installed modules or saved games.

For a converted mission under Studio control, choose **Discuss our tasks.** at its quest character, or type `!missions <name or alias>` while nearby. These menus offer acceptance, the current conversation objective and final hand-in when the game confirms their requirements. They do not need an AI response. Missions left under original control still use the adventure's original quest menus and scripts. General-import missions require Studio 1.2.0 or later and the matching adventure profile.

## Use an AI companion

For adventures created from existing modules, use Studio 1.2.0 or later and the matching converted profile. Native recruitment and quest menus remain available; supported Studio-controlled missions expose only actions allowed by their observed state. Ask a merchant what it stocks for a spoken answer, or explicitly ask to trade to open its native shop. The [conversion walkthrough](CONVERT-A-MODULE.md) explains setup and testing.

1. Recruit a party companion through their dialogue if the adventure offers recruitment, or summon your familiar/creature with your normal class abilities. Studio does not grant those abilities to every character.
2. Type `!companions` in Talk. Select the party member, familiar or summoned creature you want.
3. Choose **Talk freely with AI**, close the menu, then speak normally. Use `!end` when finished. Newly summoned creatures have conversation support enabled by default in current Studio builds, subject to the adventure's settings.
4. Use the companion menu for following, staying, guarding and inventory. These direct controls do not need an AI response.

Examples of natural requests:

- “Look inside the nearby healing supplies chest and tell me what is there.”
- “Take one healing potion from that chest and keep it in your pack.”
- “Put that potion back in the chest.”
- “Go ask Bram what swords he has for sale, then come back and tell me.”

The companion needs to reach and identify the target. Locks, ownership rules, protected equipment and the creator's settings can limit actions. Ask it to report the result; a statement that it will try is not proof that the task finished. For a familiar, `!companion familiar <message>` is also available when ordinary selection is inconvenient.

## Move items and trade

New Studio characters start with AI conversations, NPC social chat and companion visits enabled. Companions start with movement, storage inspection and item exchanges enabled. Social partners are unrestricted by default, subject to nearby/idle actors and the existing conversation budget. Creators can turn each permission off; players can further restrict their companions. Animals keep nonverbal profiles and cannot carry a spoken question to another NPC.

For an older project, its saved choices stay unchanged. In Studio's **Companions** or **Behaviors** section, choose **Apply conversation & storage defaults to this project**, review the changes, save and rebuild. Test the rebuilt module with a new game. This also clears per-character social partner restrictions; recruitment choices and animal communication styles remain as authored.

Try “Go ask the merchant what swords he has for sale,” “Look inside that chest,” or “Take one healing potion from the chest.” Companions can inspect nearby accessible containers and exchange permitted items by default. Locked, trapped or quest-gated containers remain protected, and equipped/protected items cannot be moved. Inspecting a chest alone never takes anything.

Open the companion's **Inventory** control. Select an item and use **Transfer selected**, or drag the icon to the other side of the visual inventory. Choose the quantity control when appropriate. Protected/equipped items cannot be transferred. Use page controls for longer lists. Familiars and summons use their associated storage; their disappearance does not turn natural creature weapons into transferable loot.

Talk to a merchant and choose the goods/trade option. Native merchant trading shows item icons and the game's buying/selling interface. You can also discuss stock or request a better price with AI when the adventure supports it. Actual prices and transactions are enforced by the game.

## If something does not work

- Open the AI service dashboard and confirm it shows a connected adventure and an available API key.
- Keep the game unpaused. Exit conversation menus before typing free conversation.
- Check that the creature was selected in `!companions`, or that the target NPC is nearby and AI-enabled.
- In a newly converted adventure, use `!npcs` if the original dialogue has no AI option. In Emberseal, use **Talk freely with AI** or `!talk` instead.
- For shorter or less theatrical replies, open `!aisettings` and choose **Brief**, **Plain**, actions **Off**, and questions **Only when needed**.
- After installing a rebuilt module, test it with a **new game**. Existing saves can retain old companion menus/scripts.
- If the AI service reports a quota/rate limit, check the provider's billing and limits. A successful model metadata check does not guarantee generation credit.
- For a bug report, include Studio version, module/build name, the action you tried and the displayed error. Never include an API key.
