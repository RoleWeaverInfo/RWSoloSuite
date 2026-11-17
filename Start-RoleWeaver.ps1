param([string]$AdventurePath, [switch]$Player, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$serviceScript = Join-Path $PSScriptRoot 'service.py'
if (-not (Test-Path -LiteralPath $serviceScript)) {
    $serviceScript = Join-Path $PSScriptRoot 'AI Player\service.py'
}
if (-not (Test-Path -LiteralPath $serviceScript)) {
    throw 'Role Weaver is missing. Extract the complete ZIP before starting the service.'
}
foreach ($providerVariable in @('OPENAI_API_KEY','GEMINI_API_KEY')) {
    if (-not [Environment]::GetEnvironmentVariable($providerVariable,'Process')) {
        $providerValue = [Environment]::GetEnvironmentVariable($providerVariable,'User')
        if (-not $providerValue) { $providerValue = [Environment]::GetEnvironmentVariable($providerVariable,'Machine') }
        if ($providerValue) { [Environment]::SetEnvironmentVariable($providerVariable,$providerValue,'Process') }
    }
}
$serviceArguments = @($serviceScript)
if ($AdventurePath) { $serviceArguments += @('--adventure', $AdventurePath) }
if ($Player) { $serviceArguments += '--player' }
if ($NoBrowser) { $serviceArguments += '--no-browser' }
$servicePython = Join-Path $env:LOCALAPPDATA 'Python\pythoncore-3.12-64\python.exe'
if (Test-Path -LiteralPath $servicePython) { & $servicePython @serviceArguments }
elseif (Get-Command py -ErrorAction SilentlyContinue) { & py -3 @serviceArguments }
elseif (Get-Command python -ErrorAction SilentlyContinue) { & python @serviceArguments }
else { throw 'Install Python 3.10 or newer, then run Start Role Weaver.cmd again. No additional Python packages are required.' }
exit $LASTEXITCODE
