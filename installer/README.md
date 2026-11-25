# Build release packages

The GitHub Actions `Build release packages` workflow runs Windows x64, Linux x64/ARM64 and macOS Intel/Apple Silicon builds on native runners. Branch pushes validate and retain downloadable artifacts. Version tags (`v*`) publish only after all five build jobs succeed. Plain versions such as `v1.2.0` publish a stable release marked Latest; versions with a prerelease suffix publish a prerelease without changing Latest. The tag must match `rwstudio.VERSION` and have a matching `docs/RELEASE-<version>.md` file. Update both before tagging. Never put keys, game installations or local `data` in a release.

Run the Python suite before standalone `tests/*_checks.js`. The `tests/*_fixture.js` helpers require JSON input supplied by Python tests and must not be invoked without that input. Packaged smoke checks verify the conversion/mission editor assets, the conversion and general-import guides, the current release notes, both mission runtime templates and the general-import Python modules, and an empty analysis workspace alongside the sole Emberseal example.

## Included example and release payload

All native packages and the source ZIP include only **The Emberseal of Briarwatch** from `bundled/emberseal`. `bundle.json` pins hashes for its compiled module, matching project/profile, geometry HAK, resource sources and floorplans. The packager verifies these files and creates both the embedded Share/Aurora ZIP and `The-Emberseal-of-Briarwatch-<version>.zip` for release download. Personal `data`, legacy example projects and historical playtest guides are excluded. The internal authoring template uses an `.erf` extension.

Fresh dashboards copy the curated example into the per-user workspace. Existing workspaces use **Load Emberseal example**, with a draft backup before replacement. The packaged runtime smoke test verifies the example, build, HAK and download; no model request or local game install is needed to load it. Updating the example is a maintainer operation: build it from the latest reviewed Emberseal project using `prepare_emberseal.py`, review the pinned resources and hashes, and run tests before committing. Do not replace published release assets in place; publish a new version.

Use `prepare_emberseal.py <reviewed-project.json> --game-root <NWN-folder> --output <new-staging-folder>` to build for review without changing the existing bundle. Compare the project, area resources and geometry, then replace only the pinned Emberseal files and checksum index after review. The 1.3.0 bundle must include compiled `aw_dlg_evt` and the `!aisettings` chat handler.

## Linux and macOS

Use the target OS/architecture (Ubuntu 24.04 or macOS 15 release baseline) with Python 3.13, CMake, Bison 3+ and a C++ compiler. On Mac, put Homebrew Bison on PATH; Apple's older system Bison is insufficient.

1. Install `requirements-guardrails.txt`, `requirements-platform.txt` and `pyinstaller==6.22.3` in a build environment.
2. Run `python installer/build_nwnsc.py`. This builds the pinned upstream NWScript compiler revision on the native architecture, retaining the upstream license in `vendor/nwnsc`.
3. Run tests, then `python build_native.py`. The build starts from the clean source allowlist, bundles Python/dependencies, includes source files used by generator hashing, and tests the exact packaged executable with no real API requests. Checks cover guardrails, native script compilation, static UI and local authenticated service shutdown.
4. The output is a Linux `.tar.gz` or macOS `.app` inside a symlink-preserving ZIP, plus SHA-256. No end-user Python installation is required. Mac builds are ad-hoc signed and verified, but are not Developer ID signed/notarized.

Linux keys require a running desktop Secret Service; Mac uses login Keychain. Native keyring failures fail closed instead of falling back to plaintext. OS keychain integration still warrants manual testing on the end-user desktop.

## Windows installer

The installer embeds Python in the application directory rather than installing Python globally. This preserves the source-based module generator and its resource hashes. It does not modify PATH or Python file associations. The C# console launcher uses the .NET Framework supplied with Windows 10/11 and invokes only the bundled interpreter. Users do not need the compiler or Inno Setup.

1. Run `powershell -NoProfile -ExecutionPolicy Bypass -File installer/Fetch-BuildTools.ps1` from the repository. It downloads the pinned Python archive and Inno Setup compiler, verifies SHA-256 hashes and the compiler installer's Authenticode publisher, and extracts Inno Setup in portable mode under ignored `data/installer-tools`.
2. Run `python build_installer.py` with your development Python. The Windows .NET Framework C# compiler must be present. The build uses pip to install `requirements-guardrails.txt` as Windows wheels for the embedded Python version. Network access is required during the build; end users receive these dependencies in the installer.
3. Find `Role-Weaver-Module-Studio-<version>-Setup-x64.exe`, its SHA-256 file and payload manifest in `dist`. The source ZIP remains available through `python package.py`.

The build starts from the clean release allowlist, adds the verified embedded runtime, explicitly restricts its import paths to the bundled standard library, application and private dependency directory, compiles the service launcher, probes that launcher, validates the bundled Guardrails AI with external connections disabled, and scans the payload against known credentials. Python's license and bundled dependency notices accompany the runtime. Inno Setup is a build tool and is not included in the installed application.

The stable AppId is `{C6F47CF3-CB49-4846-90F7-74FF6339D65C}`. Setup defaults to `%LOCALAPPDATA%\Programs\Role Weaver Module Studio`; the user workspace is `%LOCALAPPDATA%\RoleWeaver\ModuleStudio`. Never add that workspace to `[Files]`, `[InstallDelete]` or `[UninstallDelete]`. The service creates the named mutex `Local\RoleWeaver.ModuleStudio.Service`, which Setup checks before upgrades/uninstall. The secondary testing port uses a different mutex.

Installer tests use a dedicated directory inside the repository, with a separate `ROLEWEAVER_DATA_DIR`. Test install, start with no external Python on PATH, reinstall while closed, and uninstall. Check that a saved project/settings sentinel survives and that the service lock blocks upgrades. Do not perform recursive cleanup outside the verified test workspace. An uninstall registration is created temporarily by testing the real installer; skip such testing if an actual installed Studio is already registered.

The Windows installer is unsigned. To sign a public release, configure Inno Setup's signing support with the publisher's own certificate and signing service; never store signing credentials in the repository.

References: [Python application-local embedding](https://docs.python.org/3.13/using/windows.html#the-embeddable-package), [Python runtime release/checksums](https://www.python.org/downloads/release/python-31317/), [Inno Setup verified downloads](https://jrsoftware.org/inno-setup/downloads/verify), [portable compiler installation](https://jrsoftware.org/inno-setup/documentation/topic_technotes.htm), [per-user installation](https://jrsoftware.org/inno-setup/documentation/topic_setup_privilegesrequired.htm), [AppMutex protection](https://jrsoftware.org/inno-setup/documentation/topic_setup_appmutex.htm).
