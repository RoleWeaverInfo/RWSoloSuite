$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$toolsRoot = Join-Path $projectRoot 'data\installer-tools'
$downloads = Join-Path $toolsRoot 'downloads'
New-Item -ItemType Directory -Path $downloads -Force | Out-Null
$lock = Get-Content (Join-Path $PSScriptRoot 'runtime-lock.json') -Raw | ConvertFrom-Json
foreach ($tool in @($lock.python,$lock.inno)) {
    $file = Join-Path $downloads $tool.file
    if (-not (Test-Path -LiteralPath $file)) { Invoke-WebRequest $tool.url -OutFile $file }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $tool.sha256) {
        throw ('Checksum mismatch: '+$tool.file)
    }
}
$setup = Join-Path $downloads $lock.inno.file
$signature = Get-AuthenticodeSignature -LiteralPath $setup
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Pyrsys') {
    throw 'Inno Setup signature verification failed.'
}
$compilerDir = Join-Path $toolsRoot ('inno-'+$lock.inno.version)
if (-not (Test-Path -LiteralPath (Join-Path $compilerDir 'ISCC.exe'))) {
    $process = Start-Process -FilePath $setup -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/PORTABLE=1','/CURRENTUSER','/NOICONS',('/DIR="'+$compilerDir+'"')) -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode) { throw ('Inno Setup extraction failed: '+$process.ExitCode) }
}
Write-Output ('Verified build tools are ready in '+$toolsRoot)
