#requires -Version 5.1
<#
RubiMorph build environment setup script v3

Run as Administrator:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_rubimorph_build_env.ps1

Optional build verification:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_rubimorph_build_env.ps1 -RunBuild

Default project root:
  The repository root is resolved from this script location.

v3 fix:
  - Native command stderr is no longer merged into PowerShell's error stream.
  - unittest output such as "... ok" on stderr will not be treated as NativeCommandError.
  - External command output is captured to temp files, printed, then judged only by exit code.
#>

[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$RunBuild,
    [switch]$SkipGit
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

try {
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $OutputEncoding = [Console]::OutputEncoding
} catch {
    # Ignore console encoding failures.
}

$script:PythonFilePath = $null
$script:PythonBaseArgs = @()

function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "==== $Message ====" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Fail {
    param([string]$Message)
    throw "[ERROR] $Message"
}

function Assert-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Fail "このスクリプトは管理者権限の PowerShell で実行してください。"
    }
}

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ([string]::IsNullOrWhiteSpace($userPath)) {
        $env:Path = $machinePath
    } else {
        $env:Path = "$machinePath;$userPath"
    }
}

function Test-CommandExists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Quote-Arg {
    param([string]$Arg)

    if ($null -eq $Arg) {
        return '""'
    }

    if ($Arg -eq "") {
        return '""'
    }

    if ($Arg -notmatch '[\s"]') {
        return $Arg
    }

    return '"' + ($Arg -replace '\\(?=")', '\\' -replace '"', '\"') + '"'
}

function Join-Args {
    param([string[]]$Arguments)

    if ($null -eq $Arguments -or $Arguments.Count -eq 0) {
        return ""
    }

    $quoted = @()
    foreach ($arg in $Arguments) {
        if ($null -eq $arg) {
            $quoted += '""'
        } elseif ($arg -eq "") {
            $quoted += '""'
        } elseif ($arg -match '[\s"]') {
            $quoted += '"' + ($arg -replace '"', '\"') + '"'
        } else {
            $quoted += $arg
        }
    }

    return ($quoted -join " ")
}

function Read-FileSafe {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return ""
    }

    try {
        return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    } catch {
        try {
            return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::Default)
        } catch {
            return ""
        }
    }
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [switch]$CaptureOnly
    )

    Write-Host "> $FilePath $($Arguments -join ' ')" -ForegroundColor DarkGray

    $tempDir = Join-Path $env:TEMP ("rubimorph-env-{0}-{1}" -f $PID, ([Guid]::NewGuid().ToString("N")))
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    $stdoutPath = Join-Path $tempDir "stdout.txt"
    $stderrPath = Join-Path $tempDir "stderr.txt"

    try {
        $argString = Join-Args $Arguments
        $process = Start-Process `
            -FilePath $FilePath `
            -ArgumentList $argString `
            -NoNewWindow `
            -Wait `
            -PassThru `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath

        $stdout = Read-FileSafe $stdoutPath
        $stderr = Read-FileSafe $stderrPath

        if (-not $CaptureOnly) {
            if (-not [string]::IsNullOrWhiteSpace($stdout)) {
                Write-Host $stdout.TrimEnd()
            }
            if (-not [string]::IsNullOrWhiteSpace($stderr)) {
                # Many tools, including Python unittest, write normal progress to stderr.
                # Do not treat stderr text itself as an error.
                Write-Host $stderr.TrimEnd()
            }
        }

        return [pscustomobject]@{
            ExitCode = [int]$process.ExitCode
            Stdout = $stdout
            Stderr = $stderr
        }
    } finally {
        Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
    }
}

function Invoke-Cmd {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$ErrorMessage = "コマンドが失敗しました。"
    )

    $result = Invoke-Native -FilePath $FilePath -Arguments $Arguments
    if ($result.ExitCode -ne 0) {
        Fail "$ErrorMessage ExitCode=$($result.ExitCode) : $FilePath $($Arguments -join ' ')"
    }
}

function Invoke-CmdAllowFail {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    $result = Invoke-Native -FilePath $FilePath -Arguments $Arguments
    return [int]$result.ExitCode
}

function Get-CmdOutput {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$ErrorMessage = "コマンド出力取得に失敗しました。"
    )

    $result = Invoke-Native -FilePath $FilePath -Arguments $Arguments -CaptureOnly
    if ($result.ExitCode -ne 0) {
        Fail "$ErrorMessage ExitCode=$($result.ExitCode) : $FilePath $($Arguments -join ' ')`n$($result.Stdout)`n$($result.Stderr)"
    }

    $combined = (($result.Stdout + [Environment]::NewLine + $result.Stderr).Trim())
    return $combined
}

function Add-MachinePathIfMissing {
    param([Parameter(Mandatory = $true)][string]$Directory)

    if ([string]::IsNullOrWhiteSpace($Directory)) {
        return
    }

    if (-not (Test-Path $Directory)) {
        Write-Warn "PATH 追加対象ディレクトリが存在しません: $Directory"
        return
    }

    $fullDir = [System.IO.Path]::GetFullPath($Directory.TrimEnd('\'))
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $parts = @()
    if (-not [string]::IsNullOrWhiteSpace($machinePath)) {
        $parts = $machinePath -split ';' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    }

    $already = $false
    foreach ($part in $parts) {
        try {
            if ([System.IO.Path]::GetFullPath($part.TrimEnd('\')) -ieq $fullDir) {
                $already = $true
                break
            }
        } catch {
            # Ignore malformed PATH entries.
        }
    }

    if (-not $already) {
        $newPath = if ([string]::IsNullOrWhiteSpace($machinePath)) { $fullDir } else { "$machinePath;$fullDir" }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        Write-Ok "Machine PATH に追加: $fullDir"
    } else {
        Write-Ok "Machine PATH 追加済み: $fullDir"
    }

    Refresh-Path
}

function Ensure-Winget {
    Write-Section "winget 確認"
    Refresh-Path

    if (-not (Test-CommandExists "winget.exe")) {
        Fail "winget.exe が見つかりません。Microsoft Store の App Installer を更新してから再実行してください。"
    }

    Invoke-Cmd "winget.exe" @("--version") "winget の実行確認に失敗しました。"
    Write-Ok "winget 使用可能"
}

function Install-WingetPackage {
    param(
        [Parameter(Mandatory = $true)][string]$Id,
        [Parameter(Mandatory = $true)][string]$DisplayName,
        [switch]$MachineScope,
        [scriptblock]$PostCheck
    )

    Write-Section "$DisplayName インストール確認"
    Refresh-Path

    if ($null -ne $PostCheck) {
        try {
            if (& $PostCheck) {
                Write-Ok "$DisplayName は既に使用可能"
                return
            }
        } catch {
            # Continue to install.
        }
    }

    $baseArgs = @(
        "install",
        "--id", $Id,
        "-e",
        "--source", "winget",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--disable-interactivity"
    )

    $attempts = @()

    if ($MachineScope) {
        $attempts += ,($baseArgs + @("--scope", "machine", "--silent"))
        $attempts += ,($baseArgs + @("--scope", "machine"))
    }

    $attempts += ,($baseArgs + @("--silent"))
    $attempts += ,$baseArgs

    foreach ($args in $attempts) {
        $code = Invoke-CmdAllowFail "winget.exe" $args
        Refresh-Path

        if ($code -eq 0) {
            Write-Ok "$DisplayName の winget install は成功扱いです。"
            return
        }

        if ($null -ne $PostCheck) {
            try {
                if (& $PostCheck) {
                    Write-Ok "$DisplayName はインストール済み / 使用可能と判定しました。"
                    return
                }
            } catch {
                # Continue retry.
            }
        }

        Write-Warn "$DisplayName の winget install が ExitCode=$code で終了。別オプションで再試行します。"
    }

    Fail "$DisplayName のインストールに失敗しました。winget search $Id でパッケージ状態を確認してください。"
}

function Test-GitAvailable {
    Refresh-Path
    if (-not (Test-CommandExists "git.exe")) {
        return $false
    }
    $code = Invoke-CmdAllowFail "git.exe" @("--version")
    return ($code -eq 0)
}

function Ensure-Git {
    if ($SkipGit) {
        Write-Warn "SkipGit が指定されたため Git 確認をスキップします。"
        return
    }

    Write-Section "Git 確認"
    Refresh-Path

    if (-not (Test-GitAvailable)) {
        Install-WingetPackage -Id "Git.Git" -DisplayName "Git" -MachineScope -PostCheck { Test-GitAvailable }
    }

    Refresh-Path
    Invoke-Cmd "git.exe" @("--version") "Git の実行確認に失敗しました。"
    Write-Ok "Git 使用可能"
}

function Set-PythonInvocationIfAvailable {
    Refresh-Path

    $pyCmd = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($null -ne $pyCmd) {
        $code = Invoke-CmdAllowFail $pyCmd.Source @("-3", "-c", "import sys; print(sys.executable)")
        if ($code -eq 0) {
            $script:PythonFilePath = $pyCmd.Source
            $script:PythonBaseArgs = @("-3")
            return $true
        }
    }

    $candidates = @()

    $pythonCmd = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if ($null -ne $pythonCmd) {
        $candidates += $pythonCmd.Source
    }

    $python3Cmd = Get-Command "python3.exe" -ErrorAction SilentlyContinue
    if ($null -ne $python3Cmd) {
        $candidates += $python3Cmd.Source
    }

    $pf = [Environment]::GetEnvironmentVariable("ProgramFiles")
    $local = [Environment]::GetEnvironmentVariable("LocalAppData")
    if (-not [string]::IsNullOrWhiteSpace($pf)) {
        $candidates += (Join-Path $pf "Python312\python.exe")
        $candidates += (Join-Path $pf "Python313\python.exe")
        $candidates += (Join-Path $pf "Python314\python.exe")
    }
    if (-not [string]::IsNullOrWhiteSpace($local)) {
        $candidates += (Join-Path $local "Programs\Python\Python312\python.exe")
        $candidates += (Join-Path $local "Programs\Python\Python313\python.exe")
        $candidates += (Join-Path $local "Programs\Python\Python314\python.exe")
    }

    $candidates = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

    foreach ($candidate in $candidates) {
        $code = Invoke-CmdAllowFail $candidate @("-c", "import sys; print(sys.executable)")
        if ($code -eq 0) {
            $script:PythonFilePath = $candidate
            $script:PythonBaseArgs = @()
            return $true
        }
    }

    return $false
}

function Test-PythonAvailable {
    return Set-PythonInvocationIfAvailable
}

function Invoke-Python {
    param(
        [string[]]$Arguments = @(),
        [string]$ErrorMessage = "Python コマンドが失敗しました。"
    )

    if ([string]::IsNullOrWhiteSpace($script:PythonFilePath)) {
        if (-not (Set-PythonInvocationIfAvailable)) {
            Fail "Python が見つかりません。"
        }
    }

    Invoke-Cmd $script:PythonFilePath ($script:PythonBaseArgs + $Arguments) $ErrorMessage
}

function Get-PythonOutput {
    param(
        [string[]]$Arguments = @(),
        [string]$ErrorMessage = "Python コマンド出力取得に失敗しました。"
    )

    if ([string]::IsNullOrWhiteSpace($script:PythonFilePath)) {
        if (-not (Set-PythonInvocationIfAvailable)) {
            Fail "Python が見つかりません。"
        }
    }

    return Get-CmdOutput $script:PythonFilePath ($script:PythonBaseArgs + $Arguments) $ErrorMessage
}

function Ensure-Python {
    Write-Section "Python 確認"
    Refresh-Path

    if (-not (Test-PythonAvailable)) {
        Install-WingetPackage -Id "Python.Python.3.12" -DisplayName "Python 3.12" -MachineScope -PostCheck { Test-PythonAvailable }
    }

    if (-not (Set-PythonInvocationIfAvailable)) {
        Fail "Python が見つかりません。Python の PATH / launcher 設定を確認してください。"
    }

    Write-Ok "Python command: $script:PythonFilePath $($script:PythonBaseArgs -join ' ')"
    Invoke-Python @("-V") "Python の実行確認に失敗しました。"

    $scriptsDir = Get-PythonOutput @("-c", "import sysconfig; print(sysconfig.get_path('scripts'))") "Python Scripts ディレクトリ取得に失敗しました。"
    Add-MachinePathIfMissing $scriptsDir

    Write-Section "Python build tools インストール"
    Invoke-Python @("-m", "ensurepip", "--upgrade") "ensurepip に失敗しました。"
    Invoke-Python @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel") "pip 基本ツール更新に失敗しました。"
    Invoke-Python @("-m", "pip", "install", "--upgrade", "pyinstaller", "cyclonedx-bom") "PyInstaller / CycloneDX のインストールに失敗しました。"

    Invoke-Python @("-c", "import PyInstaller; print('PyInstaller', PyInstaller.__version__)") "PyInstaller の import 確認に失敗しました。"
    Invoke-Python @("-m", "pip", "show", "cyclonedx-bom") "cyclonedx-bom の確認に失敗しました。"

    Refresh-Path
    if (Test-CommandExists "cyclonedx-py.exe") {
        Invoke-Cmd "cyclonedx-py.exe" @("--version") "cyclonedx-py の確認に失敗しました。"
    } else {
        Write-Warn "cyclonedx-py.exe が PATH 上に見つかりません。Python Scripts は追加済みなので、新しいターミナルでは見える可能性があります: $scriptsDir"
    }

    if (-not (Test-CommandExists "py.exe")) {
        Write-Warn "py.exe が PATH 上に見つかりません。今回のスクリプトは python.exe 直指定で続行できますが、既存 build script が py -3 前提なら修正が必要です。"
    }

    Write-Ok "Python / PyInstaller / cyclonedx-bom 使用可能"
}

function Find-ISCC {
    Refresh-Path

    $cmd = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        return $cmd.Source
    }

    $pf = [Environment]::GetEnvironmentVariable("ProgramFiles")
    $pf86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")

    $candidates = @()

    if (-not [string]::IsNullOrWhiteSpace($pf86)) {
        $candidates += Join-Path $pf86 "Inno Setup 6\ISCC.exe"
        $candidates += Join-Path $pf86 "Inno Setup 7\ISCC.exe"
    }

    if (-not [string]::IsNullOrWhiteSpace($pf)) {
        $candidates += Join-Path $pf "Inno Setup 6\ISCC.exe"
        $candidates += Join-Path $pf "Inno Setup 7\ISCC.exe"
    }

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Test-InnoAvailable {
    $iscc = Find-ISCC
    return (-not [string]::IsNullOrWhiteSpace($iscc))
}

function Ensure-InnoSetup {
    Write-Section "Inno Setup / ISCC 確認"
    Refresh-Path

    $iscc = Find-ISCC
    if ([string]::IsNullOrWhiteSpace($iscc)) {
        Install-WingetPackage -Id "JRSoftware.InnoSetup" -DisplayName "Inno Setup 6" -MachineScope -PostCheck { Test-InnoAvailable }
        $iscc = Find-ISCC
    }

    if ([string]::IsNullOrWhiteSpace($iscc)) {
        Fail "ISCC.exe が見つかりません。Inno Setup を確認してください。代表的な探索先: C:\Program Files (x86)\Inno Setup 6\ISCC.exe / C:\Program Files\Inno Setup 6\ISCC.exe"
    }

    $isccDir = Split-Path -Parent $iscc
    Add-MachinePathIfMissing $isccDir

    Write-Ok "ISCC.exe: $iscc"
}

function Install-ProjectRequirementsIfAny {
    Write-Section "プロジェクト依存関係確認"

    if (-not (Test-Path $ProjectRoot)) {
        Write-Warn "ProjectRoot が見つかりません: $ProjectRoot"
        Write-Warn "システム環境だけ整備して終了します。"
        return
    }

    Push-Location $ProjectRoot
    try {
        if (Test-Path "requirements.txt") {
            Invoke-Python @("-m", "pip", "install", "--upgrade", "-r", "requirements.txt") "requirements.txt のインストールに失敗しました。"
            Write-Ok "requirements.txt インストール完了"
        } else {
            Write-Warn "requirements.txt は見つかりません。スキップします。"
        }

        if (Test-Path "pyproject.toml") {
            Write-Warn "pyproject.toml は存在します。editable install が必要な構成の場合は、別途 py -3 -m pip install -e . を検討してください。"
        }
    } finally {
        Pop-Location
    }
}

function Run-BuildVerification {
    Write-Section "RubiMorph build verification"

    if (-not (Test-Path $ProjectRoot)) {
        Fail "ProjectRoot が見つからないためビルド確認できません: $ProjectRoot"
    }

    Push-Location $ProjectRoot
    try {
        if (-not $SkipGit -and (Test-CommandExists "git.exe")) {
            Invoke-Cmd "git.exe" @("status", "--short") "git status に失敗しました。"
        }

        if (Test-Path "scripts\run_tests.cmd") {
            Invoke-Cmd "cmd.exe" @("/c", "scripts\run_tests.cmd") "scripts\run_tests.cmd に失敗しました。"
        } else {
            Write-Warn "scripts\run_tests.cmd が見つかりません。"
        }

        if ((Test-Path "src") -or (Test-Path "tests")) {
            $compileArgs = @("-m", "compileall", "-q")
            if (Test-Path "src") { $compileArgs += "src" }
            if (Test-Path "tests") { $compileArgs += "tests" }
            Invoke-Python $compileArgs "compileall に失敗しました。"
        }

        if (Test-Path "scripts\build_exe.cmd") {
            Invoke-Cmd "cmd.exe" @("/c", "scripts\build_exe.cmd") "scripts\build_exe.cmd に失敗しました。"
        } else {
            Write-Warn "scripts\build_exe.cmd が見つかりません。"
        }

        if (Test-Path "scripts\build_installer.cmd") {
            Invoke-Cmd "cmd.exe" @("/c", "scripts\build_installer.cmd") "scripts\build_installer.cmd に失敗しました。"
        } else {
            Write-Warn "scripts\build_installer.cmd が見つかりません。"
        }

        $versionPath = Join-Path $ProjectRoot "VERSION"
        if (Test-Path $versionPath) {
            $projectVersion = (Get-Content -LiteralPath $versionPath -Raw -Encoding UTF8).Trim()
        } else {
            Fail "VERSION が見つかりません: $versionPath"
        }

        $exe = Join-Path $ProjectRoot "dist\RubiMorph\RubiMorph.exe"
        $internalDir = Join-Path $ProjectRoot "dist\RubiMorph\_internal"
        $internalIcon = Join-Path $internalDir "assets\icons\rubimorph.ico"
        $sourceIcon = Join-Path $ProjectRoot "assets\icons\rubimorph.ico"
        $installer = Join-Path $ProjectRoot "dist\installer\RubiMorphSetup-$projectVersion.exe"

        if (Test-Path $exe) {
            Invoke-Cmd $exe @("--version") "RubiMorph.exe --version に失敗しました。"
            Invoke-Cmd $exe @("--list-platforms") "RubiMorph.exe --list-platforms に失敗しました。"
            Invoke-Cmd $exe @("--matrix") "RubiMorph.exe --matrix に失敗しました。"
            Write-Ok "exe 生成確認: $exe"
        } else {
            Write-Warn "exe が見つかりません: $exe"
        }

        if (Test-Path $sourceIcon) {
            Write-Ok "正式アイコン確認: $sourceIcon"
        } else {
            Fail "正式アイコンが見つかりません: $sourceIcon"
        }

        if (Test-Path $internalDir) {
            $pythonDlls = @(Get-ChildItem -Path $internalDir -Filter "python*.dll" -File -ErrorAction SilentlyContinue)
            if ($pythonDlls.Count -gt 0) {
                foreach ($dll in $pythonDlls) {
                    Write-Ok "PyInstaller 依存 DLL 確認: $($dll.FullName)"
                }
            } else {
                Fail "PyInstaller onedir の _internal に python*.dll が見つかりません: $internalDir"
            }
        } else {
            Fail "PyInstaller onedir の _internal が見つかりません: $internalDir"
        }

        if (Test-Path $internalIcon) {
            Write-Ok "同梱アイコン確認: $internalIcon"
        } else {
            Fail "PyInstaller 同梱アイコンが見つかりません: $internalIcon"
        }

        if (Test-Path $installer) {
            Write-Ok "installer 生成確認: $installer"
        } else {
            Write-Warn "installer が見つかりません: $installer"
        }
    } finally {
        Pop-Location
    }
}

Assert-Admin

$logBase = if (Test-Path $ProjectRoot) { Join-Path $ProjectRoot "logs" } else { Join-Path $env:TEMP "rubimorph-build-env" }
New-Item -ItemType Directory -Force -Path $logBase | Out-Null
$logPath = Join-Path $logBase ("setup-build-env-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))

Start-Transcript -Path $logPath -Force | Out-Null

try {
    Write-Section "RubiMorph build environment setup v3"
    Write-Host "ProjectRoot: $ProjectRoot"
    Write-Host "Log:         $logPath"

    Ensure-Winget
    Ensure-Git
    Ensure-Python
    Ensure-InnoSetup
    Install-ProjectRequirementsIfAny

    if ($RunBuild) {
        Run-BuildVerification
    } else {
        Write-Section "ビルド確認は未実行"
        Write-Host "ビルドまで一気に確認する場合は、次のように実行してください。"
        Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -RunBuild"
    }

    Write-Section "完了"
    Write-Ok "RubiMorph の Windows ビルド環境を整備しました。"
    Write-Host ""
    Write-Host "次に手動で実行するなら:"
    Write-Host "cd /d `"$ProjectRoot`""
    Write-Host "scripts\build_exe.cmd"
    Write-Host "scripts\build_installer.cmd"
    Write-Host ""
    Write-Host "PATH を確実に反映するため、この PowerShell を閉じて新しく開き直すのがおすすめです。"
} finally {
    Stop-Transcript | Out-Null
}
