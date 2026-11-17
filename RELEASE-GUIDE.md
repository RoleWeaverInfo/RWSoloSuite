# Role Weaver Module Studio 0.20.0-rc1

Create single-player Neverwinter Nights: Enhanced Edition adventures, edit them in Aurora, and add optional AI conversations, companions and merchants.

## Start Role Weaver

1. Extract the whole ZIP into a writable folder, such as Documents\Role Weaver. Do not run it from inside the ZIP or put it under Program Files.
2. Install **Python 3.10 or newer** if it is not already installed. No additional Python packages are required. This release candidate does not include a Python runtime or Windows installer.
3. Double-click **Start Role Weaver.cmd**. The service opens a browser splash screen and then Module Studio at **http://127.0.0.1:8766**. Keep the service window open while authoring or playing with AI. Closing a browser tab leaves the service running; closing the service window stops it.
4. Open **Local settings**. Check the NWN installation and user folders. Steam installs are detected where possible. Use your own installed NWN:EE game; no game installation is included. The Aurora editor is required to inspect/edit exports. The NWScript compiler is included.
5. Select OpenAI or Gemini, save your own API key, and choose separate models for authoring and in-game conversations. Keys are encrypted for your Windows account and kept in local `data/credentials.json`. You can also use `OPENAI_API_KEY` or `GEMINI_API_KEY` environment variables. API features require internet access and available provider credit.

The service never starts NWN. Open NWN yourself after starting Role Weaver, then select your module or saved game. Clicking Start Role Weaver again reuses the running service. The splash uses the included Role Weaver artwork; the dashboard uses a blue theme.

## Build and share

A fresh installation starts with a blank area workspace. Add a floorplan and description, review the inferred objects and scale, and apply the generated proposal. Edit rooms, connections, furnishings, materials and lighting, then use **Update generated area** or **Open in Aurora**. **Install area for testing** installs a separate offline test module; start NWN yourself to test it.

Create an adventure when ready to add story, NPCs, quests and encounters. Use **Build & share** to export a complete ZIP. Keep the `.mod`, generated/imported `hak/` files and `.rwproject.json` together. Third-party HAKs may have their own sharing conditions. Authors should test the module in Aurora and NWN before distributing it.

## Play a shared adventure

1. Start NWN once to establish its user folder, then close it. Extract the **entire adventure ZIP**.
2. Run **Start Role Weaver.cmd** from the adventure folder while NWN is closed. This starts/reuses the service, registers that exact AI profile, and installs the module and included HAKs. It backs up a differing installed module. If a separate service is already running, its configured NWN user folder is used.
3. Configure your provider key in **Module Studio → Local settings**, if needed. The AI service status page links back to Studio. Keep the service window open.
4. Open NWN separately, start a new single-player game in the module, or load a compatible save. Older saves retain their embedded area/script resources; start a new game to test a newly rebuilt module.

For manually installed modules, copy `.mod` into your NWN user `modules` folder and included HAKs into `hak`. Import the matching `.rwproject.json` using **AI service status**; this registers the build without replacing an author's draft. Each different build needs its matching profile. Native menus, authored dialogue and quest logic remain playable offline. AI conversations need the service and a provider key. Keep NWN unpaused while waiting for a response.

## Updating and troubleshooting

Close the old service before upgrading, and extract this release into a **new folder**. Keep a backup of your previous `data` folder. To retain settings, credentials, projects and build profiles, copy that whole folder to the new installation while both services are stopped. Encrypted keys work only for the same Windows user. Retained compiler paths may point to the old folder; check Settings after moving an installation. Do not distribute your `data` folder.

- **Older service running:** close its service window, then start this release. Do not close NWN without saving.
- **Python not found:** install Python 3.10+ for Windows, then retry the launcher.
- **No AI response:** check AI service status, provider key/model, provider credit, the NWN user-folder setting and the imported build profile. Loading a `.mod` alone does not start Role Weaver.
- **Missing HAK:** extract the complete adventure ZIP and run its service launcher while NWN is closed, or copy the included HAKs manually.
- **Port 8766 occupied:** close the other Role Weaver service or conflicting application before retrying.

Release candidate checks cover code, native export and packaging. Final visuals, pathfinding and gameplay still need an author playtest. This ZIP contains no personal projects, saved API keys, downloaded content packs or saved games. See RELEASE-NOTES.md and ROLE-WEAVER-LICENSE.txt; the bundled compiler's license is under vendor/nwnsc.
