# How to convert an existing NWN module

Role Weaver Module Studio 1.3.0 can analyse an existing Neverwinter Nights 1 / Enhanced Edition module and create a separate copy with AI conversations, native merchant support and companion capabilities. It preserves the original maps and placements. Original quests remain in control unless you explicitly enable a supported experimental mission conversion.

**The Emberseal of Briarwatch is the only included example.** Supply your own legally obtained community modules and required content packs. Snow Hunt and its generated copies are not included or hosted by this project. Permission to play a module does not automatically grant permission to redistribute a converted copy.

## 1. Prepare Studio and the adventure

1. Install [Studio 1.2.0 or later](https://github.com/RoleWeaverInfo/RWSoloSuite/releases/latest) for your computer. Windows, Linux and Mac application packages include Python and the NWScript compiler.
2. Start NWN once and close it. Start Studio and check **Local settings → Local NWN folders and compiler**. Set the NWN installation and user folders. Keep the supplied compiler selected unless you have configured another compatible compiler.
3. Extract the adventure download. Locate its `.mod`, required `.hak` packs and any custom `.tlk`. Keep an untouched original outside Studio's workspace. Extraction must happen before import; select the `.mod`, not its ZIP.
4. To use live AI or optional profile generation, configure your own OpenAI or Gemini key in **Local settings → Set up your AI**. Local analysis, mission review and compilation do not require an AI request. **Explain with AI** and **Generate detailed AI profiles** use the authoring model; conversations during play use the gameplay model.

See [installation and key setup](INSTALLATION.md) for platform-specific paths. NWNX and a persistent-world server are not required for the added AI service. Conversion cannot remove an original module's own dependency on unsupported extensions.

## 2. Import and review the report

1. Open **Module Conversion** in the left navigation.
2. Select the **Module file**. If packs came with the adventure, enter their parent folder in **Dependency folder (optional)**; subfolders are searched.
3. Click **Import and analyse**. You can instead expand **Or use a path on this computer**, enter the full `.mod` path, and select **Analyse local file**.
4. Keep Studio running while it creates a private snapshot and report. When complete, select the report under **Saved analyses**.
5. Review **Overview**, **Dependencies**, **Characters**, **Quests**, **Dialogue** and **Scripts**. Resolve missing packs before converting. Reimport after supplying resources that were missing during analysis.

The analyser can inspect compiled `.ncs` scripts when original `.nss` source is absent. It shows disassembly, engine calls and recoverable constants; it does not reconstruct arbitrary source code or prove that a quest works. Warnings identify unresolved or incomplete evidence. **Optional AI explanation → Explain with AI** can help interpret selected evidence, but its conclusions need review.

## 3. Review the story and quests

Open **Missions & storyline**. Select a mission in the dropdown or overview, then open its **Stage map**. Click a card or use **Jump to stage**. Pan and zoom the diagram, or use **Fit** and **Focus**.

There are three different kinds of editing:

| Edit | Effect in the new module |
| --- | --- |
| Private storyline, stage labels, notes and review arrows | Helps the creator understand the adventure; does not change quest execution or enter NPC prompts |
| Native journal quest name and entry text | Changes displayed journal wording; preserves original triggers, stages and rewards |
| Supported editable Studio mission, explicitly enabled | Changes executable objectives and rewards for that supported quest |

**Public setting and adventure premise** is supplied to gameplay AI, so keep unrevealed plot twists out of it. Entry numbering alone does not establish quest order. Use script/dialogue evidence to review connections; a review arrow is not a new in-game trigger. Use **Check edits**, then **Save conversion edits**.

### Optional: change a supported mission's objectives and rewards

For your first conversion, leaving **Keep original module quest** selected provides the broadest compatibility. The general importer in **1.2.0** can copy uniquely tagged journal missions into inactive drafts. It shows script conflicts separately from editable objective/reward fields. Both creators and players need the updated Studio for general-import mission profiles.

1. Choose **Copy to editable Studio mission**. This makes an inactive draft; it does not turn on new rules automatically.
2. Open **Mission settings & rewards**. Choose the quest giver, edit the agreement and completion text, and review recovered gold/XP calls before choosing completion totals.
3. Select objective cards. Resolve **Needs review** objectives, choose native targets, and add, remove or reorder objectives. Supported types are possession, visit, talk and defeat. The final hand-in returns to the chosen quest giver. Journal numbers are not proof of chronological order.
4. Review the agreement and both review checkboxes. Use **Check edits**. Script conflicts can require original control even when the draft is editable; incomplete drafts can be saved in original mode.
5. Where supported, select **Use editable Studio mission (experimental)** and accept the warning. Choose independently for every mission. Save, then rebuild a separate copy and start a new game. Test native conditions as well as the edited quest.

The [general importer guide](GENERAL-MISSION-IMPORT.md) explains supported script patterns, blockers and backups. This does not automatically reconstruct branching logic or every reward type. The older [dedicated adapter](MODULE-ANALYSER.md#optional-studio-control-rival-ogre-mages) remains compatible with its original source fingerprint; that third-party adventure is not bundled.

To return to native execution, choose **Keep original module quest**, save and rebuild. The inactive draft is retained. This does not migrate an existing save game.

## 4. Set up AI characters, merchants and companions

1. Open **AI profiles & build** and expand **Review creature profiles**.
2. Review aliases, roles, backgrounds, personalities, public knowledge and speech/nonverbal settings. Turn individual creatures' AI support off if desired. Keep secrets out of public knowledge.
3. Optionally choose **Generate detailed AI profiles**. This uses your authoring model to expand the recovered descriptions and safe opening dialogue, up to six characters per request. The dashboard shows the number of requests remaining before you start. Large modules can take many minutes. Generated backgrounds are creative additions, not recovered author canon. Review them before building.
4. Store-linked characters receive merchant support where the original scripts can be resolved. Check the detected store links. AI uses the original store, prices and access rules; it does not invent a replacement shop.
5. Keep companion support enabled for already recruited party members, familiars and summons, or disable it. Native recruitment and dismissal remain under the original adventure's control.
6. Click **Save conversion edits**.

Converted NPCs remember native conversation lines and player replies actually reached during play. Unseen dialogue branches are not treated as known facts. Dynamically generated actors, external HAK dialogue and unusual scripted shops can require additional work; review the report's limitations.

### Profile generation progress and recovery

The progress panel shows profiles saved, percentage complete, the current batch and characters, elapsed time, and time spent waiting for the model. Only finished, saved batches advance the bar. The editor stays in place while progress updates; Studio continues working if you leave the page, provided the service stays running.

Each successful batch is saved immediately. **Pause after current batch** lets the current request finish and saves its results before stopping further requests. **Resume detailed AI profiles** continues with unfinished characters, preserving completed profiles and your edits. Provider failures or a service restart also leave completed batches available to resume. **Regenerate all profiles…** asks for confirmation and makes new API requests to replace role, background, personality and motivation for every character. Public knowledge, mission edits and other conversion settings are retained.

Authoring no longer has Studio's former hard-coded 60-request hourly cap. Gameplay limits in **Guardrails & usage** still apply to gameplay, and your provider's own quotas and billing limits still apply to authoring. If the provider rejects a batch, resolve the reported problem and resume; Studio does not retry indefinitely. A failed generation from an older Studio version cannot recover batches that version never saved.

## 5. Build and install a separate copy

1. In **AI profiles & build → Create an AI-enabled copy**, choose a distinct module filename, for example `pools_of_radiance_ai_edition`. Studio allows up to **64 characters before `.mod`**: lowercase letters, digits and underscores, starting with a letter. Omit the extension. The separate **Copy title** is the name displayed in NWN. Keep the original filename for the untouched source. Existing saved profiles keep their filenames until you edit them and build a new copy.
2. Confirm the dependency folder and click **Create AI-enabled copy**. Compilation and preservation checks run locally. Fix any reported errors before installation.
3. The resulting build offers its `.mod`, matching `.rwproject.json`, share ZIP and preservation report. `preservation.json` records which resources remain identical and any deliberate mission edits. Supported mission takeover also includes backups of replaced scripts in the export.
4. Close NWN and choose **Install copy locally**. Keep Role Weaver running with its AI service enabled.
5. Start NWN and begin a **new game** using the copied module's title. Existing saves embed older module resources and do not acquire these changes.

Each rebuild creates a matching AI profile. Always install/register the `.rwproject.json` from the same build as the `.mod`. Editing the dashboard alone does not update an installed module. Aurora can edit a copied module on Windows, but another Studio conversion starts from the imported original and does not merge those Aurora edits.

Large conversions use cached NPC configuration and indexed profile lookups. The regular heartbeat updates the session and companion tasks; detailed merchant stock and companion observations are collected for conversation requests instead of every heartbeat. These improvements apply to newly built conversions. To update an older copy, rebuild from its saved profiles, install the new `.mod` and matching sidecar, and start a new game. Restarting Studio alone cannot replace scripts embedded in a module or saved game. You do not need to generate the AI profiles again.

## 6. Test conversations, stores, companions and quests

- Talk through an NPC's original introduction, then choose **Talk freely with AI** where offered. Close the dialogue and speak in Talk. Alternatively use `!talk <alias> <message>` near that character. The exported play instructions list aliases. Use `!end` to finish.
- If an NPC has no AI dialogue option, close the dialogue and type **`!npcs`** in Talk. Select the nearby character, then speak normally. This also works for profiled characters with no dialogue and dialogues supplied by HAKs. The list uses the actual creatures' names and distances, so identically named NPCs can be selected individually. It refreshes only when opened or requested. Characters must be visible, within 12 metres, AI-enabled and available outside combat, cutscenes and active dialogue; familiar/summon controls remain under `!companions`.
- Ask about something the NPC just said. Keep the game unpaused while waiting for the service.
- Use **`!aisettings`** to change reply length, speaking style, action descriptions and follow-up questions during play. Defaults are Normal, Characterful, Occasional and Conversational. These preferences are saved with the game; see [AI response settings](PLAYER-GUIDE.md#adjust-ai-replies-while-playing).
- Open a merchant's original shop once, then ask what it stocks. “What do you sell?” should produce a spoken answer; “Show me your wares” requests the store. Original introductions and conditional shop choices still apply.
- Recruit a companion normally, or use your character's familiar/summon ability. Type `!companions`, select it and test AI chat, inventory and permitted errands. Quest items, ownership, combat, locked/trapped containers and equipped items retain their protections.
- Test native quests, area transitions, rest/death rules, stores and saving/loading. For an enabled Studio mission, also test every objective, missing required items, rewards and repeated hand-ins. Compare with the original adventure.

An AI statement is not proof that an item moved or a reward was paid. Check the actual journal, inventory, gold and XP. See [the player guide](PLAYER-GUIDE.md) for more examples.

## 7. Share or remove your conversion

Share the complete exported ZIP only when the original authors' licenses permit it. Players need NWN:EE, Studio 1.2.0 or later, required packs, and their own API key for live AI. On another computer, extract the ZIP, copy `.mod` into the NWN user `modules` folder, `.hak` into `hak`, and `.tlk` into `tlk`. Start Studio and register the matching `.rwproject.json` on **AI service status → Register an adventure** before starting NWN.

Use **Delete exported copy** to remove a local export, and **Delete analysis** to remove the imported snapshot/report. Both ask for confirmation. These controls do not delete the original download, installed modules, saves or retained runtime registrations. Official Studio releases include Emberseal only; your conversion workspace is not uploaded automatically.

## Quick troubleshooting

| Symptom | What to check |
| --- | --- |
| Missing HAK or TLK | Extract the packs, set the dependency folder, then reimport/rebuild |
| Matching adventure build not found | Register the sidecar from that exact module build; test with a new game |
| No AI reply | Studio running, AI service enabled, key/model access and quota, gameplay guardrails, game unpaused |
| Companion replies always say they were discarded | Rebuild with the updated companion handler, install the matching copy and start a new game. Modules with catch-all speech listeners previously treated ordinary speech as a new order. Actual orders, ownership changes and changed companion preferences still cancel outdated replies. Saved AI profiles can be reused |
| Profile generation stopped | Read the error, resolve any provider limit, then choose **Resume detailed AI profiles**. Completed batches are kept. If the message says Studio's 60-request hourly limit, restart an updated Studio; that authoring cap has been removed |
| No AI option in a dialogue | Close the conversation and use `!npcs`. Ordinary action-free exits receive an AI option regardless of their wording or language; forced quest/payment choices stay unchanged |
| Studio control unavailable | Read the mission's script conflicts. Supply missing dependencies and reimport, or retain original control; dynamic/shared/unsupported effects can require a dedicated adapter |
| Changed rewards do not appear | Save conversion edits, rebuild, install the new copy and start a new game |
| Large converted module pauses regularly | Rebuild with the updated converter and start a new game. If it persists, compare the same location in the original module and check the NWN log for `TOO MANY INSTRUCTIONS`. Original module scripts also run on the heartbeat |

For technical coverage and preservation details, see [Module Conversion reference](MODULE-ANALYSER.md).
