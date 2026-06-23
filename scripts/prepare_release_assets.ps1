param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

function Get-ProjectVersion {
    param([string]$Root)

    $versionPath = Join-Path $Root "VERSION"
    if (-not (Test-Path $versionPath)) {
        throw "VERSION was not found: $versionPath"
    }

    $value = (Get-Content -LiteralPath $versionPath -Raw -Encoding UTF8).Trim()
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "VERSION is empty: $versionPath"
    }
    return $value
}

function Assert-File {
    param([string]$Path)

    if (-not (Test-Path $Path -PathType Leaf)) {
        throw "Required file was not found: $Path"
    }
}

function Assert-Directory {
    param([string]$Path)

    if (-not (Test-Path $Path -PathType Container)) {
        throw "Required directory was not found: $Path"
    }
}

$ProjectRoot = (Resolve-Path $ProjectRoot).Path
if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = Get-ProjectVersion -Root $ProjectRoot
}

$distRoot = Join-Path $ProjectRoot "dist\RubiMorph"
$installer = Join-Path $ProjectRoot "dist\installer\RubiMorphSetup-$Version.exe"
$releaseDir = Join-Path $ProjectRoot "release"
$portableZip = Join-Path $releaseDir "RubiMorphPortable-$Version.zip"
$thirdPartyLicensesZip = Join-Path $releaseDir "RubiMorphThirdPartyLicenses-$Version.zip"
$portableStage = Join-Path $releaseDir "portable-staging"
$portableRoot = Join-Path $portableStage "RubiMorph"
$licensesStage = Join-Path $releaseDir "licenses-staging"
$sbomSource = Join-Path $ProjectRoot "dist\sbom\rubimorph.cdx.json"
$sbomDest = Join-Path $releaseDir "rubimorph.cdx.json"
$checksumsPath = Join-Path $releaseDir "SHA256SUMS.txt"
$notesPath = Join-Path $releaseDir "release-notes.md"
$notesTemplatePath = Join-Path $ProjectRoot "docs\release-notes-template.md"

Assert-Directory $distRoot
Assert-File (Join-Path $distRoot "RubiMorph.exe")
Assert-File (Join-Path $distRoot "RubiMorphGUI.exe")
Assert-File (Join-Path $distRoot "LICENSE")
Assert-File (Join-Path $distRoot "THIRD_PARTY_NOTICES.md")
Assert-Directory (Join-Path $distRoot "LICENSES")
Assert-File (Join-Path $distRoot "LICENSES\Python-3.14.3-LICENSE.txt")
Assert-File $notesTemplatePath
Assert-Directory (Join-Path $distRoot "_internal")
if (-not (Get-ChildItem -LiteralPath (Join-Path $distRoot "_internal") -Filter "python*.dll" -File)) {
    throw "python*.dll was not found under dist\RubiMorph\_internal"
}
Assert-File $installer

New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
Get-ChildItem -LiteralPath $releaseDir -Filter "RubiMorphSetup-*.exe" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force
Get-ChildItem -LiteralPath $releaseDir -Filter "RubiMorphPortable-*.zip" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force
Get-ChildItem -LiteralPath $releaseDir -Filter "RubiMorphThirdPartyLicenses-*.zip" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force
Remove-Item -LiteralPath $portableStage -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $licensesStage -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $portableZip -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $thirdPartyLicensesZip -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $checksumsPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $notesPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $sbomDest -Force -ErrorAction SilentlyContinue

$releaseInstaller = Join-Path $releaseDir (Split-Path $installer -Leaf)
Copy-Item -LiteralPath $installer -Destination $releaseInstaller -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "LICENSE") -Destination (Join-Path $releaseDir "LICENSE") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "THIRD_PARTY_NOTICES.md") -Destination (Join-Path $releaseDir "THIRD_PARTY_NOTICES.md") -Force

New-Item -ItemType Directory -Force -Path $portableRoot | Out-Null
Copy-Item -Path (Join-Path $distRoot "*") -Destination $portableRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "README.md") -Destination (Join-Path $portableRoot "README.md") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "LICENSE") -Destination (Join-Path $portableRoot "LICENSE") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "THIRD_PARTY_NOTICES.md") -Destination (Join-Path $portableRoot "THIRD_PARTY_NOTICES.md") -Force
Compress-Archive -Path $portableRoot -DestinationPath $portableZip -CompressionLevel Optimal -Force

New-Item -ItemType Directory -Force -Path $licensesStage | Out-Null
Copy-Item -LiteralPath (Join-Path $ProjectRoot "THIRD_PARTY_NOTICES.md") -Destination $licensesStage -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "LICENSE") -Destination $licensesStage -Force
Copy-Item -Path (Join-Path $ProjectRoot "LICENSES") -Destination (Join-Path $licensesStage "LICENSES") -Recurse -Force
Compress-Archive -Path (Join-Path $licensesStage "*") -DestinationPath $thirdPartyLicensesZip -CompressionLevel Optimal -Force

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($portableZip)
try {
    $zipEntries = $zip.Entries.FullName | ForEach-Object { $_ -replace "\\", "/" }
    $requiredZipEntries = @(
        "RubiMorph/RubiMorph.exe",
        "RubiMorph/RubiMorphGUI.exe",
        "RubiMorph/README.md",
        "RubiMorph/LICENSE",
        "RubiMorph/THIRD_PARTY_NOTICES.md",
        "RubiMorph/LICENSES/Python-3.14.3-LICENSE.txt"
    )
    foreach ($entry in $requiredZipEntries) {
        if ($zipEntries -notcontains $entry) {
            throw "Portable ZIP is missing required entry: $entry"
        }
    }
    if (-not ($zipEntries | Where-Object { $_ -like "RubiMorph/_internal/python*.dll" })) {
        throw "Portable ZIP is missing RubiMorph/_internal/python*.dll"
    }
} finally {
    $zip.Dispose()
}

Remove-Item -LiteralPath $portableStage -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $licensesStage -Recurse -Force -ErrorAction SilentlyContinue

Push-Location $ProjectRoot
try {
    & cmd.exe /c scripts\generate_sbom.cmd
    if ($LASTEXITCODE -ne 0) {
        throw "scripts\generate_sbom.cmd failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

Assert-File $sbomSource
Copy-Item -LiteralPath $sbomSource -Destination $sbomDest -Force

$hashTargets = @($releaseInstaller, $portableZip, $thirdPartyLicensesZip, $sbomDest)
$checksumLines = foreach ($path in $hashTargets) {
    $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $path
    "{0} *{1}" -f $hash.Hash.ToLowerInvariant(), (Split-Path $path -Leaf)
}
$checksumLines | Set-Content -LiteralPath $checksumsPath -Encoding ASCII

$releaseNotes = (Get-Content -LiteralPath $notesTemplatePath -Raw -Encoding UTF8).Replace("{{VERSION}}", $Version)
$releaseNotes | Set-Content -LiteralPath $notesPath -Encoding UTF8

Get-ChildItem -LiteralPath $releaseDir -File |
    Sort-Object Name |
    Select-Object Name, Length, FullName
