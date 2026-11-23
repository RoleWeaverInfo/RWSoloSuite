# The Emberseal of Briarwatch

The sole example included with Role Weaver Module Studio 1.2.0. It uses the latest revised Briarwatch maps, rebuilt with current service checks, companion permissions and NPC conversation defaults. The module filename is **rw_ember_v3.mod**. The project is **emberseal_demo**.

## Story and setting

On the eve of the harvest fair, goblin raiders steal Briarwatch's Emberseal, an amber stone that steadies the boundary wards. Queen Elowen Vale asks a visiting adventurer to recover it before nightfall, promising **300 gold**. Gather clues and supplies, follow the road through danger, defeat Skarn Ashhand in Ember Hollow, retrieve the seal from his strongbox and return it to the queen.

The adventure is designed for **levels 3–4 and a two-member party**. Sergeant Hale Ward is an optional recruit. Familiars and summons attach their profiles to creatures summoned through your character's normal abilities; the module does not grant summoning spells.

| Area | Included layout and content |
| --- | --- |
| Briarwatch Keep | Enclosed indoor rooms, furnished throne hall, dais and carpet, assistants and guards |
| Briarwatch Gate and Green Road | Walled stone market courtyard with four merchants, gate, farm, forest and road; three outdoor encounters |
| Ember Hollow | Enclosed cave rooms, lookout encounter, healing cache and Skarn's final chamber |

There are **three areas, fourteen rooms, fifteen named characters, five combat encounters and two linked quests**. Each area includes its annotated revision-2 floorplan inside the project.

## Start playing

1. Install and start Role Weaver Module Studio. On a fresh workspace, Emberseal is already selected. On an existing workspace, choose **Load Emberseal example** in the sidebar. A prior Emberseal draft is backed up before replacement; other work is kept.
2. Set your NWN installation/user folders and your own Gemini or OpenAI key. Keep the service running for live AI conversations.
3. With NWN closed, open **Build & share** and choose **Play in NWN** on the included build. It installs the module and required HAK and opens character selection. No AI generation or module compilation is needed.
4. Start a new game. Talk to Queen Elowen in the throne room, then use the journal and NPC directions. Native dialogue menus also advance the quests without AI.

For a separate download, get **The-Emberseal-of-Briarwatch-1.2.0.zip** from the [release page](https://github.com/RoleWeaverInfo/RWSoloSuite/releases). Extract all files. The service launcher registers the matching `.rwproject.json` and installs the module/HAK when supported. Otherwise copy the `.mod` into your NWN `modules` folder and every included `.hak` into `hak`, then import the matching profile on the AI service page. Start NWN yourself. See [installation instructions](INSTALLATION.md).

The `.mod` alone is insufficient: its generated geometry HAK is required. No CEP or other downloaded content pack is required. You still need your own NWN:EE installation. Older saved games keep their old resources; use a new game for this build.

## Talk, trade and use companions

Choose **Talk freely with AI**, close the dialogue and speak in Talk. Direct examples include `!talk elowen how can I help?` and `!talk bram what swords do you sell?`. The market merchants are Mara Reed (baker), Bram Ironstock (armorer), Tavin Quill (wizard) and Sister Alia Dawn (cleric). Native merchant menus remain available.

Use `!companions` to select a companion. Speaking companions can be asked “Go ask the merchant what swords he has for sale,” “Look inside that chest,” or “Take one healing potion.” AI dialogue, owner-directed visits, accessible storage inspection and exchanges are enabled in the example. Animals remain nonverbal. Locked/trapped containers and protected items retain their native restrictions. See the [player guide](PLAYER-GUIDE.md).

## Study or edit the example

Select the project and inspect **Story & direction**, **Characters**, **Quests & endings**, and the three areas' floorplans and visual editor. Download **Share / Aurora ZIP** to keep the module, profile, HAK, resource sources and geometry sources together. Install the HAK before opening the module in Aurora on Windows. Save Aurora changes to a separate module copy; they are not imported back into Studio.

Use a new project ID/module filename for your own adventure. Rebuilding Emberseal creates another shareable build; the pinned included example remains available through the sidebar. [Create an adventure](CREATE-AN-ADVENTURE.md) explains how to begin with ChatGPT story and floorplan drafts.

The current revision passed structural checks and native compilation. Its latest script changes still need ordinary in-game/Aurora playtesting; successful compilation does not certify every route or encounter.
