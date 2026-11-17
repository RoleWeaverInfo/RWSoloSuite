# Build the Windows installer

The installer embeds Python in the application directory rather than installing Python globally. This preserves the source-based module generator and its resource hashes. It does not modify PATH or Python file associations. The C# console launcher uses the .NET Framework supplied with Windows 10/11 and invokes only the bundled interpreter. Users do not need the compiler or Inno Setup.

1. Run `powershell -NoProfile -ExecutionPolicy Bypass -File installer/Fetch-BuildTools.ps1` from the repository. It downloads the pinned Python archive and Inno Setup compiler, verifies SHA-256 hashes and the compiler installer's Authenticode publisher, and extracts Inno Setup in portable mode under ignored `data/installer-tools`.
2. Run `python build_installer.py` with your development Python. The Windows .NET Framework C# compiler must be present. No pip dependencies are required.
3. Find `Role-Weaver-Module-Studio-<version>-Setup-x64.exe`, its SHA-256 file and payload manifest in `dist`. The source ZIP remains available through `python package.py`.

The build starts from the clean release allowlist, adds the verified embedded runtime, explicitly restricts its import paths to the bundled standard library and application, compiles the service launcher, probes that launcher and scans the payload against known credentials. Python's license and bundled dependency notices accompany the runtime. Inno Setup is a build tool and is not included in the installed application.

The stable AppId is `{C6F47CF3-CB49-4846-90F7-74FF6339D65C}`. Setup defaults to `%LOCALAPPDATA%\Programs\Role Weaver Module Studio`; the user workspace is `%LOCALAPPDATA%\RoleWeaver\ModuleStudio`. Never add that workspace to `[Files]`, `[InstallDelete]` or `[UninstallDelete]`. The service creates the named mutex `Local\RoleWeaver.ModuleStudio.Service`, which Setup checks before upgrades/uninstall. The secondary testing port uses a different mutex.

Installer tests use a dedicated directory inside the repository, with a separate `ROLEWEAVER_DATA_DIR`. Test install, start with no external Python on PATH, reinstall while closed, and uninstall. Check that a saved project/settings sentinel survives and that the service lock blocks upgrades. Do not perform recursive cleanup outside the verified test workspace. An uninstall registration is created temporarily by testing the real installer; skip such testing if an actual installed Studio is already registered.

The candidate is unsigned. To sign a public release, configure Inno Setup's signing support with the publisher's own certificate and signing service; never store signing credentials in the repository.

References: [Python application-local embedding](https://docs.python.org/3.13/using/windows.html#the-embeddable-package), [Python runtime release/checksums](https://www.python.org/downloads/release/python-31317/), [Inno Setup verified downloads](https://jrsoftware.org/inno-setup/downloads/verify), [portable compiler installation](https://jrsoftware.org/inno-setup/documentation/topic_technotes.htm), [per-user installation](https://jrsoftware.org/inno-setup/documentation/topic_setup_privilegesrequired.htm), [AppMutex protection](https://jrsoftware.org/inno-setup/documentation/topic_setup_appmutex.htm).
