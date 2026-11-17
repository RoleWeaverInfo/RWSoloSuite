# Compatibility for existing shortcuts. Releases use Start Role Weaver.cmd.
param([switch]$Player)
& (Join-Path $PSScriptRoot 'Start-RoleWeaver.ps1') -Player:$Player
exit $LASTEXITCODE
