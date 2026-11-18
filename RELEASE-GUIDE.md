# Role Weaver Module Studio 0.20.0-rc2

Create single-player Neverwinter Nights: Enhanced Edition adventures, edit them in Aurora, and add optional AI conversations, companions and merchants.

## Start Role Weaver

1. Run **Role-Weaver-Module-Studio-0.20.0-rc2-Setup-x64.exe** on Windows 10/11 (64-bit). Setup installs Role Weaver and its private Python runtime for your Windows account. You do not need to install Python separately.
2. Choose whether to add a desktop shortcut. Start **Role Weaver Module Studio** from the Start menu or that shortcut. The browser shows the splash and then the dashboard at **http://127.0.0.1:8766**.
3. Keep the Role Weaver service window open while authoring or playing with AI. Closing a browser tab leaves the service running; closing the service window stops it. The installer does not start NWN.
4. Open **Local settings**. Check the NWN installation and user folders. Steam installs are detected where possible. Use your own installed NWN:EE game; no game installation is included. The Aurora editor is required to inspect/edit exports. The NWScript compiler is included.
5. Select OpenAI or Gemini, save your own API key, and choose separate models for authoring and in-game conversations. Keys are encrypted for your Windows account and kept in the workspace file `credentials.json`. You can also use `OPENAI_API_KEY` or `GEMINI_API_KEY` environment variables. API features require internet access and available provider credit.

The service never starts NWN. Open NWN yourself after starting Role Weaver, then select your module or saved game. Clicking Start Role Weaver again reuses the running service. The splash uses the included Role Weaver artwork; the dashboard uses a blue theme.

## Guardrails and token usage

Open **Guardrails & usage** in the sidebar for gameplay dialogue protections, request limits, an optional daily token stop, and separate persistent token reports for gameplay and module creation. Checks run locally without additional AI review calls. See [GUARDRAILS-AND-USAGE.md](GUARDRAILS-AND-USAGE.md) for defaults, limits and data retention.

## Build and share

A fresh installation starts with a blank area workspace. Add a floorplan and description, review the inferred objects and scale, and apply the generated proposal. Edit rooms, connections, furnishings, materials and lighting, then use **Update generated area** or **Open in Aurora**. **Install area for testing** installs a separate offline test module; start NWN yourself to test it.

Create an adventure when ready to add story, NPCs, quests and encounters. Use **Build & share** to export a complete ZIP. Keep the `.mod`, generated/imported `hak/` files and `.rwproject.json` together. Third-party HAKs may have their own sharing conditions. Authors should test the module in Aurora and NWN before distributing it.

## Play a shared adventure

1. Install Role Weaver Module Studio using Windows Setup. Start NWN once to establish its user folder, then close it. Extract the **entire adventure ZIP**.
2. Run **Start Role Weaver.cmd** from the adventure folder while NWN is closed. This starts/reuses the service, registers that exact AI profile, and installs the module and included HAKs. It backs up a differing installed module. If a separate service is already running, its configured NWN user folder is used.
3. Configure your provider key in **Module Studio → Local settings**, if needed. The AI service status page links back to Studio. Keep the service window open.
4. Open NWN separately, start a new single-player game in the module, or load a compatible save. Older saves retain their embedded area/script resources; start a new game to test a newly rebuilt module.

For manually installed modules, copy `.mod` into your NWN user `modules` folder and included HAKs into `hak`. Import the matching `.rwproject.json` using **AI service status**; this registers the build without replacing an author's draft. Each different build needs its matching profile. Native menus, authored dialogue and quest logic remain playable offline. AI conversations need the service and a provider key. Keep NWN unpaused while waiting for a response.

## Updating and troubleshooting

Close the service before running a newer Setup. Projects, builds, asset caches, settings and saved keys are stored in **%LOCALAPPDATA%\RoleWeaver\ModuleStudio**, separately from the program files. Setup updates the application and bundled runtime. Uninstall removes the application and shortcuts while preserving this workspace. Keys remain encrypted for the same Windows account. You can back up the workspace folder while the service is stopped.

To migrate from a previous source ZIP, close both services and copy that ZIP's entire `data` folder into the installed workspace location above before first launch. If a workspace already exists there, back it up before merging. Check game/user folders and the compiler path in Settings afterward. Do not distribute your workspace or saved keys.

The **source ZIP** is still available for developers: extract it to a writable folder and use **Start Role Weaver.cmd** with Python 3.10–3.13. Create a local `.venv` and install `requirements-guardrails.txt` as described in [GUARDRAILS-AND-USAGE.md](GUARDRAILS-AND-USAGE.md). The source launcher prefers that environment. Source checkouts keep `data` beside the source; installed copies use the per-user location. `ROLEWEAVER_DATA_DIR` is an optional explicit workspace override for testing or a separate workspace.

- **Older service running:** close its service window, then start this release. Do not close NWN without saving.
- **Python not found:** use the Windows Setup installer, which includes Python. Only the source ZIP needs a separate Python installation.
- **No AI response:** check AI service status, provider key/model, provider credit, the NWN user-folder setting and the imported build profile. Loading a `.mod` alone does not start Role Weaver.
- **Missing HAK:** extract the complete adventure ZIP and run its service launcher while NWN is closed, or copy the included HAKs manually.
- **Port 8766 occupied:** close the other Role Weaver service or conflicting application before retrying.

Release candidate checks cover code, native export and packaging. Final visuals, pathfinding and gameplay still need an author playtest. The installer and source ZIP contain no personal projects, saved API keys, downloaded content packs or saved games. See RELEASE-NOTES.md and ROLE-WEAVER-LICENSE.txt; the bundled compiler's license is under vendor/nwnsc.
