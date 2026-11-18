param([string]$AdventurePath, [switch]$Player, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
foreach ($providerVariable in @('OPENAI_API_KEY','GEMINI_API_KEY')) {
    if (-not [Environment]::GetEnvironmentVariable($providerVariable,'Process')) {
        $providerValue = [Environment]::GetEnvironmentVariable($providerVariable,'User')
        if (-not $providerValue) { $providerValue = [Environment]::GetEnvironmentVariable($providerVariable,'Machine') }
        if ($providerValue) { [Environment]::SetEnvironmentVariable($providerVariable,$providerValue,'Process') }
    }
}
$serviceArguments = @()
if ($AdventurePath) { $serviceArguments += @('--adventure', (Resolve-Path -LiteralPath $AdventurePath).Path) }
if ($Player) { $serviceArguments += '--player' }
if ($NoBrowser) { $serviceArguments += '--no-browser' }
$installedExe = Join-Path $PSScriptRoot 'Role Weaver Module Studio.exe'
if (-not (Test-Path -LiteralPath $installedExe) -and $AdventurePath) {
    $registered = Get-ItemProperty 'HKCU:\Software\RoleWeaver\ModuleStudio' -ErrorAction SilentlyContinue
    if ($registered.InstallDir) { $installedExe = Join-Path $registered.InstallDir 'Role Weaver Module Studio.exe' }
}
if (Test-Path -LiteralPath $installedExe) {
    & $installedExe @serviceArguments
    exit $LASTEXITCODE
}
$serviceScript = Join-Path $PSScriptRoot 'service.py'
if (-not (Test-Path -LiteralPath $serviceScript)) { $serviceScript = Join-Path $PSScriptRoot 'AI Player\service.py' }
if (-not (Test-Path -LiteralPath $serviceScript)) { throw 'Role Weaver is missing. Install Role Weaver Module Studio or extract the complete adventure ZIP.' }
$pythonArguments = @('-B',$serviceScript) + $serviceArguments
$servicePython = Join-Path (Split-Path -Parent $serviceScript) '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $servicePython)) { $servicePython = Join-Path $env:LOCALAPPDATA 'Python\pythoncore-3.12-64\python.exe' }
if (Test-Path -LiteralPath $servicePython) { & $servicePython @pythonArguments }
elseif (Get-Command py -ErrorAction SilentlyContinue) { & py -3 @pythonArguments }
elseif (Get-Command python -ErrorAction SilentlyContinue) { & python @pythonArguments }
else { throw 'Install Role Weaver Module Studio using its Windows Setup installer. It includes Python. Developers using the source ZIP can instead install Python 3.10+.' }
exit $LASTEXITCODE
