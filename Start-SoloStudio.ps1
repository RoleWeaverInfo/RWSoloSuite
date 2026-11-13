param([switch]$Player)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$studioUrl = 'http://127.0.0.1:8766'
$studioPage = if ($Player) { "$studioUrl/player" } else { $studioUrl }
try {
    $studioState = Invoke-RestMethod "$studioUrl/api/state" -TimeoutSec 2
    if ($studioState.version -and $studioState.catalog) {
        if ($Player) {
            Invoke-RestMethod "$studioUrl/api/bridge" -Method Post -ContentType 'application/json' -Headers @{'X-Studio-Token'=$studioState.csrf} -Body '{"enabled":true}' | Out-Null
        }
        Start-Process $studioPage
        exit 0
    }
} catch { }
if (-not $env:OPENAI_API_KEY) {
    $env:OPENAI_API_KEY = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY','User')
    if (-not $env:OPENAI_API_KEY) { $env:OPENAI_API_KEY = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY','Machine') }
}
$studioPython = Join-Path $env:LOCALAPPDATA 'Python\pythoncore-3.12-64\python.exe'
$studioArguments = @('studio.py','--open')
if ($Player) { $studioArguments += '--player' }
if (Test-Path -LiteralPath $studioPython) { & $studioPython @studioArguments }
elseif (Get-Command py -ErrorAction SilentlyContinue) { & py -3 @studioArguments }
elseif (Get-Command python -ErrorAction SilentlyContinue) { & python @studioArguments }
else { throw 'Install Python 3.10 or newer, then run this launcher again. No Python packages are required.' }
