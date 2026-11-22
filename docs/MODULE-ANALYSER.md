# Module Conversion

This feature is available in the current source checkout; it is not included in the published 1.0.0 packages yet.

Open **Module Conversion** in the dashboard sidebar. The main workspace has its own scrollbar; scroll over the report to reach its lower sections. Choose an existing Neverwinter Nights 1 / Enhanced Edition `.mod` file and click **Import and analyse**. Alternatively, expand **Or use a path on this computer**, enter its full path, and click **Analyse local file**. A `.rwproject.json` file is not required.

Studio makes a private snapshot in its workspace under `module-analysis`. It reads the module without executing its scripts, loading NWN, changing maps, adding AI NPCs or overwriting your editable project. You can leave the page while the analysis runs and return to select the saved report. Keep the service running until it finishes.

If the downloaded adventure has its own dependency folders, enter their parent folder in **Dependency folder (optional)**. Studio searches its subfolders for declared HAK and TLK names. Local-path imports automatically search beside the original module when no explicit dependency folder is supplied. These per-import searches do not change your global content settings or install the packs. Folder search is bounded to eight levels and 50,000 entries, with a warning when exceeded.

## What you can review

- **Overview:** recovered module description, authored story excerpts, resource counts, missing dependencies and limits.
- **Areas:** names, tags, tilesets and tile dimensions; no geometry is regenerated.
- **Characters:** placed creatures and creature blueprints, authored descriptions, dialogue references, classes, faction IDs, inventory resource references and linked scripts. Personality and knowledge are only recoverable to the extent the author expressed them in descriptions and dialogue.
- **Encounters:** native encounter triggers and blueprints, spawn limits and creature definitions. Fixed placed enemies appear under Characters; scripted spawns appear in the script findings.
- **Quests:** journal categories and stages, completion flags, authored text and links to compiled-script evidence. A journal entry number alone does not establish progression order.
- **Dialogue:** NPC and player text, starting nodes, reply links, condition scripts and action scripts. Conditional branches may contradict each other because they represent different playthroughs.
- **Scripts:** compiled `.ncs` disassembly, engine function calls, locally traceable constant arguments, string literals and relative branch targets. Select **Inspect** to see details and download the full decoded listing. Source `.nss` and debug-symbol `.ndb` presence is reported; debug symbols are not interpreted in this version.
- **Dependencies:** declared HAKs and custom talk tables, with found/missing status.

Sections support search and pagination. **Download JSON report** exports the recovered inventory and findings. The script panel shows bounded excerpts; its disassembly download includes every instruction decoded within the stated budget.

## Compiled scripts and reliability

The analyser reads NWScript bytecode directly; original `.nss` source is not required. With a configured NWN installation, it uses that installation's `nwscript.nss` definitions to name engine actions. Without those definitions, it displays numeric action IDs. Quest journal text, dialogue and creature records still work without an installation.

This is static analysis, not full source recovery or a verified walkthrough. Literal arguments are tracked conservatively within a basic block; `null` means unresolved. Calls may be conditional, delayed or unreachable. An `AddJournalQuestEntry` call with a recovered quest tag is stronger evidence than a matching string constant; the report labels this distinction. Dynamic script names, external databases, missing resources and complex state can leave gaps. Unsupported instructions and malformed resources are reported instead of guessed.

The report inventories module definitions first and searches declared HAKs and installed game resources for missing references. It does not simulate runtime override precedence, NWSync, campaign databases or custom engine extensions. Put required HAKs in the configured custom-content folder or NWN `hak` folder and custom TLKs in NWN's `tlk` folder. Configure **Local settings** before importing. Reimport after adding missing dependencies to produce a new snapshot/report.

Uploads accept `.mod` archives below 4 GB. Inspection budgets are separate from upload size: 15,000 resources, 2,000 dialogues, 2,500 scripts, 256 MB of parsed resource data, 64 MB of compiled script data, 8 MB per script and 250,000 instructions per script. Truncation and unsupported data are disclosed. These limits apply only to the analyser, not the area-design HAK catalog.

## Optional AI interpretation

Local inspection does not call an AI provider or need an API key. Expand **Optional AI explanation** and click **Explain with AI** to request a story and quest interpretation from your configured authoring model. Selected text and script excerpts are sent to that provider using your saved key. Usage counts as module creation; the provider's billing and quota rules apply.

The explanation cites numbered evidence entries that you can expand. Missing citations are rejected. Valid citations are not proof that an interpretation is correct: review inferred motives, chronology and quest conditions against the recovered text and scripts. The AI receives bounded excerpts, not every byte of a large module. Module text is treated as untrusted content rather than instructions.

## Keeping and removing reports

**Delete analysis** asks for confirmation and removes only that report and its private snapshot. It does not delete the original module, installed modules, saves or Studio projects. Reports are local and are not automatically shared. Respect the module author's permissions before distributing extracted content.

Importing alone is read-only. Conversion is a separate action described below. Deleting an analysis does not delete its exported AI copies. Use **Delete exported copy** in the conversion panel before deleting its analysis if you also want to remove the export. Installed modules and runtime registrations are retained. Keep the original module outside the analysis workspace.

## Create an AI-enabled copy

1. Select a completed analysis. Check missing dependencies and script warnings first. Set the installed NWN folder and NWScript compiler in **Local settings**.
2. Expand **Create an AI-enabled copy**. Choose a distinct module filename and supply the folder containing the original HAK/TLK files. Subfolders are searched. Conversion refuses missing dependencies and conflicting Role Weaver resource names.
3. Check **Public setting and adventure premise**, then choose **Generate detailed AI profiles**. This optional step uses your configured authoring model and API key, with tokens counted as authoring usage. It creates roles, personalities, motivations and everyday backgrounds from each character's authored description and unconditional opening dialogue. Generated background is creative elaboration, not recovered author canon. Generation replaces these four fields; edited public knowledge is retained. If generation fails, the saved draft is retained.
   Expand **Review creature profiles** to review those fields and their source references, enable or disable AI per creature, edit its alias and public knowledge, and choose speech or nonverbal reactions. Do not put secrets into public knowledge. **Save AI profile** keeps these settings independently of authoring projects.
   Characters whose linked scripts open native stores receive **AI merchant abilities** by default. Their profiles show the detected store links and allow you to disable merchant support or requests to negotiate. Stock stays in the original module; the converter does not create a replacement shop.
4. Keep companion support enabled for already recruited party members, familiars and summons, or turn it off. Recruitment, dismissal, party limits and their original quest/XP scripts remain native.
5. Click **Create AI-enabled copy**. Studio compiles its added runtime, verifies the exported resources and registers the matching runtime profile. No LLM call or payment is needed for this step. It never runs the imported scripts during conversion or starts NWN.
6. With NWN closed, choose **Install copy locally**. Start the updated Role Weaver service before NWN, configure your own API key, enable the AI service, and start a **new game** in the copied module. Existing saves of the original module do not contain the additions.

The ZIP contains the converted `.mod`, matching `.rwproject.json`, required HAK/TLK files, added NWScript sources, play instructions and `preservation.json`. The original pack filenames and bytes are retained. Installation refuses to replace a different pack with the same name. Keep `.mod` and `.rwproject.json` together. On another computer, install the updated Studio, import the sidecar on **AI service status**, and copy the module to NWN's `modules` folder and its dependencies to `hak` and `tlk`. The published 1.0.0 service cannot load these converted profiles yet.

Aurora can edit the copied module. Save Aurora edits under another name: converting again starts from the imported original, not from those edits. Do not import a converted profile into the area authoring editor; it describes an existing native module, not a generated room graph.

## Play the converted adventure

Use original NPC dialogue for quests, stores, recruitment and dismissal. At eligible ordinary dialogue exits there is an added **Talk freely with AI** choice. Select it, close the menu and speak in Talk. Alternatively, stand near a creature and use `!talk <alias> <message>`, or a unique character name followed by a colon. The play instructions list the aliases. `!end` stops the conversation.

The AI receives its public setting, identity, background and personality, plus a save-local memory of native NPC lines and player replies actually reached. Recording happens throughout the original conversation, even if you select AI chat later or use a chat command. Ordinary single-line greetings also gain an AI option; forced quest choices remain intact. Selecting AI chat no longer replaces the earlier conversation with just one line.

Unvisited dialogue branches are stored as a retrieval library in the sidecar, but are filtered out before an AI request. Relevant previously reached lines can be recalled beyond the recent transcript. Separate NPC instances have separate memories. Recruited companions, familiars and summons can discuss the owner's recent conversations as information shared by the owner. This supplies mission context without treating unseen journal entries or compiled-script constants as facts. It does not read arbitrary native journal state or infer a quest completion from a static script call. Original menus still handle quest progression and rewards.

Memory is bounded to the recent transcript and up to 1,024 observed node IDs per NPC. Native custom text tokens have no getter in standard NWScript; unresolved substitutions are omitted rather than invented. External HAK conversations are not rewritten and therefore are not automatically recorded. Rebuild the copy and begin a new game to enable the new hooks; old saves cannot reconstruct conversations that happened before recording existed.

For converted merchants, open the original shop once before asking AI about its current stock. AI can then discuss the observed goods. Requests to browse, buy or negotiate return to the character's original trading conversation; select its shop option to trade. Native access conditions, Appraise checks, prices, discounts, gold and item transfers remain authoritative. AI does not create new discounts or sell items outside that interface. Detection follows linked scripts, including recovered literal script calls; dynamically computed or unresolved store links may need manual review. Ambiguous store links are not guessed.

Recruit an ally through the original adventure first, then use `!companions` for AI chat, follow/stay/guard, visual inventory and optional container/visit errands. Familiars and summoned creatures attach to their real native owners. Animals use nonverbal responses by default. Combat, possession, ownership, protected-item and locked/trapped-container checks remain enforced. Native companion dialogue, combat AI and death handlers are retained; the added dialogue/death hooks chain to the originals. Native rest, death, resurrection, item-acquisition and area scripts are not replaced.

## Preservation and testing limits

Every original area, creature, encounter, journal, faction, item and original source/compiled script resource must remain byte-for-byte identical. The copy changes the module name/identity and four module event assignments, appends AI choices at safe exits, and wraps spoken dialogue-node actions to record conversation memory. Each assigned original action is called exactly once by its wrapper. Original dialogue text, indices, conditions, existing links and quest fields remain intact. The converter reconstructs and compares the original dialogue structure after removing its additions and wrappers. Original module load, client entry, heartbeat and chat handlers are also called once when assigned. Automatic ambient patrol/social control and AI quest rewards are not injected.

Conversion currently supports module archives up to 512 MB and 1,000 distinct creature identities; external HAKs are streamed without that size limit. Only inventoried creatures receive profiles; dynamically created creatures from unexamined external resources may need a later import extension. Familiar/summon template support is independent. Duplicate creatures retain their native tags and use per-instance chat history; ambiguous nearby aliases are rejected rather than selecting an arbitrary actor. Menus belonging to external HAKs are not rewritten. Some dialogues have no safe exit to extend, so use chat commands or companion controls instead.

Static checks are not a playthrough guarantee. Custom engine extensions, dynamic module transitions, overrides, event-context assumptions and quest-specific inventory mechanics need manual testing. The original missing-script warnings still apply. Test transitions, quest acceptance/completion/rewards, stores, rest/death, native recruitment/dismissal, saving/loading and requested item transfers before sharing. The original adventure remains playable without AI; the added AI conversations require the updated service and your API key. Gameplay guardrails and token tracking apply normally.

The local **Snow Hunt** test uses its original 17 areas, three journal quests and required content packs. The merchant and conversation-memory test copy is `rw_snow_trade.mod`; begin a new game in it, rather than loading an older save. Talk with the original quest characters, recruit Durthan through his original menu, then use `!companions`. Test a familiar or summon separately. Vikan, the city merchant and the starting equipment character have detected native shops: open their original shop, ask AI about its goods, and ask to trade again. Compare native prices, quest rewards, XP changes, cold/rest rules and transitions with the original adventure. Snow Hunt and its content packs are local test inputs, not bundled Studio examples or release assets; obtain the original authors' permission before redistributing them.
