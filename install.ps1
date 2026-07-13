param(
    [string]$InstallRoot = "$env:LOCALAPPDATA\ZMLC\zmlc-router"
)

$ErrorActionPreference = "Stop"
$repo = "rthgit/zmlc-router"
$asset = "zmlc-router-windows-x64.zip"
$base = "https://github.com/$repo/releases/latest/download"
$temporary = Join-Path ([System.IO.Path]::GetTempPath()) ("zmlc-install-" + [guid]::NewGuid())

function Find-Codex {
    $versioned = Get-ChildItem (Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin") `
        -Filter codex.exe -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -ne (Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin\codex.exe") } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($versioned) { return $versioned.FullName }
    $direct = Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin\codex.exe"
    if (Test-Path $direct) { return $direct }
    $command = Get-Command codex -ErrorAction SilentlyContinue
    if ($command -and $command.Source -notmatch "\\WindowsApps\\") {
        return $command.Source
    }
    throw "Codex was not found. Install Codex or set it on PATH before installing ZMLC."
}

try {
    $cosign = Get-Command cosign -ErrorAction SilentlyContinue
    if (-not $cosign) {
        throw "cosign is required for Sigstore verification: https://docs.sigstore.dev/cosign/system_config/installation/"
    }
    New-Item -ItemType Directory -Force -Path $temporary | Out-Null
    $archive = Join-Path $temporary $asset
    $checksum = "$archive.sha256"
    $bundle = "$archive.sigstore.json"
    Invoke-WebRequest "$base/$asset" -OutFile $archive
    Invoke-WebRequest "$base/$asset.sha256" -OutFile $checksum
    Invoke-WebRequest "$base/$asset.sigstore.json" -OutFile $bundle

    $expected = ((Get-Content $checksum -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
    $actual = (Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "SHA-256 mismatch for $asset" }
    & $cosign.Source verify-blob `
        --bundle $bundle `
        --certificate-identity-regexp "^https://github.com/$repo/.github/workflows/release.yml@refs/tags/v.*$" `
        --certificate-oidc-issuer "https://token.actions.githubusercontent.com" `
        $archive
    if ($LASTEXITCODE -ne 0) { throw "Sigstore verification failed" }

    $staging = Join-Path $temporary "extracted"
    Expand-Archive $archive -DestinationPath $staging
    $source = Get-ChildItem $staging -Directory | Select-Object -First 1
    if (-not $source) { throw "Release archive has no root directory" }
    $codex = Find-Codex
    $zmlc = Join-Path $source.FullName "plugins\zmlc-router\bin\zmlc.exe"
    & $zmlc doctor
    if ($LASTEXITCODE -ne 0) { throw "ZMLC doctor failed before installation" }

    if (Test-Path $InstallRoot) { Remove-Item -Recurse -Force $InstallRoot }
    New-Item -ItemType Directory -Force -Path (Split-Path $InstallRoot) | Out-Null
    Move-Item $source.FullName $InstallRoot
    & $codex plugin remove "zmlc-router@zmlc-public" 2>$null
    & $codex plugin marketplace remove "zmlc-public" 2>$null
    & $codex plugin marketplace add $InstallRoot
    if ($LASTEXITCODE -ne 0) { throw "Could not add the ZMLC marketplace" }
    & $codex plugin add "zmlc-router@zmlc-public"
    if ($LASTEXITCODE -ne 0) { throw "Could not install the ZMLC plugin" }
    & (Join-Path $InstallRoot "plugins\zmlc-router\bin\zmlc.exe") doctor
    if ($LASTEXITCODE -ne 0) { throw "Installed ZMLC doctor failed" }
    Write-Host "ZMLC installed. Start a new Codex task to load the plugin."
    Write-Host "Uninstall: codex plugin remove zmlc-router@zmlc-public; codex plugin marketplace remove zmlc-public"
}
finally {
    if (Test-Path $temporary) { Remove-Item -Recurse -Force $temporary }
}
