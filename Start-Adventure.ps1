param(
    [string]$Module = 'rw_packfix',
    [string]$ModuleFile,
    [string]$Sidecar,
    [string]$GameRoot,
    [string]$UserDir,
    [switch]$Resume,
    [switch]$ChooseMode,
    [switch]$Offline,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$launcherScript = Join-Path $PSScriptRoot 'play.py'
if (-not (Test-Path -LiteralPath $launcherScript)) {
    $launcherScript = Join-Path $PSScriptRoot 'AI Player\play.py'
}
if (-not (Test-Path -LiteralPath $launcherScript)) { throw 'The AI Player runtime is missing. Extract the complete adventure ZIP before launching.' }
if (-not $env:OPENAI_API_KEY) { $env:OPENAI_API_KEY = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY','User') }
if (-not $env:OPENAI_API_KEY) { $env:OPENAI_API_KEY = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY','Machine') }
$launcherArguments = @($launcherScript, '--module', $Module)
if ($ModuleFile) { $launcherArguments += @('--module-file', $ModuleFile) }
if ($Sidecar) { $launcherArguments += @('--sidecar', $Sidecar) }
if ($GameRoot) { $launcherArguments += @('--game-root', $GameRoot) }
if ($UserDir) { $launcherArguments += @('--user-dir', $UserDir) }
if ($Resume) { $launcherArguments += '--resume' }
if ($ChooseMode) { $launcherArguments += '--choose-mode' }
if ($Offline) { $launcherArguments += '--offline' }
if ($CheckOnly) { $launcherArguments += '--check-only' }
$launcherPython = Join-Path $env:LOCALAPPDATA 'Python\pythoncore-3.12-64\python.exe'
if (Test-Path -LiteralPath $launcherPython) { & $launcherPython @launcherArguments }
elseif (Get-Command py -ErrorAction SilentlyContinue) { & py -3 @launcherArguments }
elseif (Get-Command python -ErrorAction SilentlyContinue) { & python @launcherArguments }
else { throw 'Install Python 3.10 or newer. No additional Python packages are required.' }
exit $LASTEXITCODE
