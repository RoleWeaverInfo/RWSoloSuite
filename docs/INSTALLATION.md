# Install Role Weaver Module Studio

Download a package from [Releases](https://github.com/RoleWeaverInfo/RWSoloSuite/releases). Choose the operating system and processor **of the computer running Studio**. The application packages include Python, the NWScript compiler and local Guardrails AI validators. No separate Python installation is needed.

| Computer | Download | Release baseline |
| --- | --- | --- |
| Windows Intel/AMD 64-bit | `Setup-x64.exe` | Windows 10/11 x64 |
| Linux Intel/AMD 64-bit | `Linux-x64.tar.gz` | Ubuntu 24.04 or compatible newer desktop |
| Linux ARM64 | `Linux-arm64.tar.gz` | Ubuntu 24.04 ARM64 or compatible newer desktop |
| Mac with Intel processor | `macOS-x64.zip` | macOS 15 or later |
| Mac with Apple Silicon (M-series) | `macOS-arm64.zip` | macOS 15 or later |

These are release candidates. Native automated checks cover packaged startup, local dashboard requests, compiler output and offline guardrails. Full NWN gameplay on every operating system is not yet certified. ARM64 Studio support does not imply that NWN itself runs natively on Linux ARM64. Use a game installation supported by its publisher. Aurora Toolset runs on Windows; Linux and Mac can author/build standard modules and transfer them to Windows for Aurora editing.

You need your own Neverwinter Nights: Enhanced Edition installation and its game data to build and play modules. Game files, third-party HAK packs and API keys are not included. A browser and internet access are needed for AI requests. Conventional authored dialogue, quests and menus can work without AI.

## Windows

1. Run the downloaded `Setup-x64.exe`. Setup installs for your current Windows account.
2. Start **Role Weaver Module Studio** from the Start menu or desktop shortcut.
3. Keep its service window open while you use AI. The browser opens the splash screen and then the dashboard at `http://127.0.0.1:8766`.

## Linux

1. Extract the matching `.tar.gz` into a folder you own. Keep the entire `RoleWeaverModuleStudio` folder together.
2. Open that folder and run `RoleWeaverModuleStudio`. From a terminal in the extracted folder, use `./RoleWeaverModuleStudio`.
3. Keep the application running while playing. If the browser does not open, visit `http://127.0.0.1:8766` yourself.
4. To save keys, use an unlocked desktop Secret Service keyring, such as GNOME Keyring. Minimal/headless systems may need their distribution's keyring and D-Bus desktop packages. Studio will report when secure storage is unavailable; it will not silently save plaintext keys. Environment variables are an alternative.

## macOS

1. Open **About This Mac** to check Intel versus Apple Silicon, then extract the matching ZIP.
2. Move **Role Weaver Module Studio.app** into Applications (or your user's Applications folder). Launch it there and leave it running while playing.
3. The candidate is ad-hoc signed, not Developer ID signed or Apple notarized. macOS may block its first launch. After checking that you downloaded the intended release, use Apple's **Privacy & Security → Open Anyway** procedure if available. Do not disable Gatekeeper globally. See [Apple's guidance for apps outside the App Store](https://support.apple.com/en-us/102445).
4. Allow Studio to access its saved key in your login Keychain when requested.

## First setup on every platform

1. Start NWN once, then close it. This creates the game's user folder.
2. In Studio, open **Local settings**. Check **NWN installation** and **NWN user folder**. Steam installations are detected when possible. Point the installation at the folder containing the game's `data` directory. A custom Steam library or non-Steam installation may need manual selection.
3. In **Set up your AI**, choose Gemini or OpenAI. Click **Get an API key** to open the provider's official website. Create your own key, paste it into Studio, and click **Save key locally**. Never put a key in the storyline, a project or a shared ZIP.
4. Choose a gameplay conversation model and a separate authoring model, then **Save and use**. Recommended choices are shown in the interface. Gemini offers a limited free tier for eligible models/accounts; OpenAI API usage is paid. ChatGPT subscriptions do not supply API credit. Check the linked pricing and provider terms before use; availability, quotas and prices can change.
5. **Check model access** checks model metadata only. It cannot establish whether billing, generation permissions or free quota will allow your next request.
6. Set gameplay limits in **Guardrails & token usage**. Usage is tracked separately for gameplay and Studio generation. Provider billing remains the authoritative record.

Keys are protected with Windows DPAPI, macOS Keychain, or Linux Secret Service. Project exports never include them. `OPENAI_API_KEY` and `GEMINI_API_KEY` environment variables are also supported; a saved key for that provider takes precedence. Removing the saved key does not revoke it at the provider.

## Play an adventure

**The Emberseal of Briarwatch is the sole included example.** Fresh installations load its editable project and compiled build automatically. Existing workspaces can choose **Load Emberseal example** in the sidebar; a previous Emberseal draft is backed up, and other projects remain. In **Build & share**, use **Play in NWN** or **Share / Aurora ZIP** without generating or compiling anything first. The release also offers **The-Emberseal-of-Briarwatch-0.21.0-rc3.zip** separately. See the [Emberseal guide](EMBERSEAL.md) for its story, characters and route. Earlier trial modules are not bundled; upgrades do not delete your personal modules or saved games.

Extract the **entire** adventure ZIP. Keep its matching `.mod` and `.rwproject.json` together. With NWN closed:

1. On Windows, run the adventure's **Start Role Weaver.cmd** to register and install it through the installed service. On Linux/Mac, use **Start Role Weaver.sh** / **Start Role Weaver.command** if your installed app is found; otherwise use the manual steps below.
2. Manual setup: copy `.mod` to the NWN user folder's `modules` directory, and included `.hak` files to its `hak` directory. Install any dependencies named in `dependencies.json` separately, respecting their authors' licenses.
3. Start Studio, open **AI service**, and import the matching `.rwproject.json` under **Register an adventure**. This keeps the adventure's AI profiles available without replacing an authoring draft.
4. Start NWN yourself. Select the installed module for a new game, or load a save from that same build. Loading a module does **not** start the Role Weaver service. Keep NWN unpaused while waiting for AI replies.

Default NWN user folders are `Documents/Neverwinter Nights` on Windows/Mac and `~/.local/share/Neverwinter Nights` on Linux (or under `XDG_DATA_HOME`). Verify yours in Settings.

## Stop, update and back up

Close NWN before replacing installed module files. Use **AI service → Stop Role Weaver** or close its terminal window before updating Studio. Closing the browser alone does not stop the service.

In versions with the **Update software** button (sidebar or AI service page), choose **Check for updates**, then **Download update**. Studio selects the package for your operating system and architecture and verifies its SHA-256 digest against GitHub's release metadata. After saving your project and exiting NWN, choose **Install update and restart**. This updates the service and dashboard together. Windows uses the per-user installer; Linux/Mac keep the previous application beside the replacement as a backup. The browser reconnects after restart. If it does not, start Role Weaver normally and check the workspace's `updates/<operation>/update.log` (and `installer.log` on Windows).

Stable installations receive stable releases; release candidates can receive newer candidates or stable releases. Automatic installation is for native packages with a writable installation folder and an external workspace. Source checkouts can check releases but are never overwritten. Update source separately after committing or backing up local changes. The earlier 0.21.0-rc1 packages predate this button; install 0.21.0-rc3 or newer once before using automatic updates.

The official release repository is public: updates and downloads do not require a GitHub sign-in or a shared access key. If GitHub temporarily rate-limits anonymous checks, retry later or use **Open official releases**. An existing GitHub CLI sign-in can also be used when available; no developer GitHub credential is bundled.

For a module exported in this workspace, **Build & share → Shareable builds → Play in NWN** installs that exact build and its packaged dependencies, registers its matching AI profile, enables the service, and starts NWN at character selection. Save and exit an already-running NWN first. This button starts a new adventure; use NWN's own **Load Game** menu for existing saves. The normal Role Weaver startup shortcuts still start only the service. Native game detection supports Windows, macOS and Linux installations; Wine/Proton-only installations should be launched through their own game launcher.

User workspaces are separate from application files:

| Platform | Workspace |
| --- | --- |
| Windows | `%LOCALAPPDATA%\RoleWeaver\ModuleStudio` |
| macOS | `~/Library/Application Support/RoleWeaver/ModuleStudio` |
| Linux | `$XDG_DATA_HOME/RoleWeaver/ModuleStudio`, normally `~/.local/share/RoleWeaver/ModuleStudio` |

Back up that folder while Studio is stopped. Windows Setup preserves it during upgrades/uninstall. On Linux/Mac, replace the application folder/app with the new version. OS-protected keys are tied to your user/keyring; enter them again after moving to another computer. Source checkouts use their local `data` directory unless `ROLEWEAVER_DATA_DIR` is set.

## Common problems

- **Matching adventure build not found:** import the `.rwproject.json` supplied with that exact `.mod`. Start a new game to test a regenerated module; old saves keep older resources.
- **No AI response:** check service status, your active provider/key/model, quota/credit, gameplay guardrails, and that the game is unpaused. Do not post your API key in a bug report.
- **Service not connected in-game:** start or update Role Weaver, enable its AI service, and verify the NWN user folder. Newly rebuilt modules provide `!studio` to recheck and automatically report reconnection. The module cannot launch a desktop application itself. Older saves retain their earlier scripts.
- **Another version is running:** stop the old service before launching the new one.
- **Cannot save a key on Linux/Mac:** unlock the OS keyring and retry, or set the provider environment variable before starting Studio.
- **Aurora unavailable:** export from Build & share and open the module on Windows. Studio's visual editor works on all three platforms.
- **Download inaccessible:** the official repository is public. Check the release URL and your network connection; if GitHub is rate-limiting requests, retry later.

Next: [Playing with AI](PLAYER-GUIDE.md) · [Create an adventure with ChatGPT and Studio](CREATE-AN-ADVENTURE.md).
