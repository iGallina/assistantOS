# assistantOS — everything the Windows installer does, for the current user only (no admin, no UAC prompt).
# Run by the Inno Setup wizard (install/assistantOS.iss) one step at a time; also runnable by hand:
#   powershell -NoProfile -ExecutionPolicy Bypass -File bootstrap.ps1 [-Step git,uv,core,claude,paseo,setup,page] [-Ref main]
# Every step is idempotent: running it again skips what is already in place. Log: %LOCALAPPDATA%\assistantOS\install.log
# Downloads are pinned and checked against each project's published SHA-256; uv and Claude Code use their official
# installers, as install.ps1 always did. Files fetched here carry no "downloaded from the internet" mark, so SmartScreen
# never stops Paseo's unsigned installer.
param(
    [string[]]$Step = @('git', 'uv', 'core', 'claude', 'paseo', 'setup', 'page'),
    [string]$Ref = ''   # a branch or tag to install instead of the newest release (testing only)
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Base = Join-Path $env:LOCALAPPDATA 'assistantOS'
$Core = Join-Path $Base 'core'
$Repo = 'https://github.com/iGallina/assistantOS.git'
$Arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { 'arm64' } else { 'x64' }
$Pins = @{
    git   = @{
        x64   = @('https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.2/MinGit-2.56.0.2-64-bit.zip', 'da35e72aa21c005a5a0d298cfbae110bc1609a815730ea0dde84b01a1b3cd3be')
        arm64 = @('https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.2/MinGit-2.56.0.2-arm64.zip', '38b33dc6024026e3315cf88ab2cfea65205bbd7bb3a8e824bd21c8ad4fe609a7')
    }
    paseo = @{
        x64   = @('https://github.com/getpaseo/paseo/releases/download/v0.11.1/Paseo-Setup-0.11.1-x64.exe', 'f772b7c915d541f72e4c5129f30a09f9542f45c6803345c3fd3747d6143c71b6')
        arm64 = @('https://github.com/getpaseo/paseo/releases/download/v0.11.1/Paseo-Setup-0.11.1-arm64.exe', '82720f9c51be65aa9c3e731769342cba1274be03aed326c403444957f59e4f0c')
    }
}
New-Item -ItemType Directory -Force -Path $Base | Out-Null
$Log = Join-Path $Base 'install.log'

function Log([string]$msg) { Add-Content -Path $Log -Value ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $msg) -Encoding UTF8 }
function Has([string]$cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Run([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'   # PowerShell 5.1 turns any stderr line of a native program into an error
    $out = & $exe @argv 2>&1 | Out-String
    Log "$exe $($argv -join ' ') -> exit $LASTEXITCODE`n$out"
    if ($LASTEXITCODE -ne 0) { throw "$exe $($argv[0]) falhou (código $LASTEXITCODE)" }
}
function Fetch([string]$name) {
    $url, $sha = $Pins[$name][$Arch]
    $file = Join-Path $env:TEMP (Split-Path $url -Leaf)
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $file
    $got = (Get-FileHash -Algorithm SHA256 $file).Hash.ToLower()
    if ($got -ne $sha) { Remove-Item $file -Force; throw "${name}: SHA-256 não confere ($got) — nada foi instalado" }
    Log "${name}: $url ok"
    $file
}
function AddUserPath([string]$dir) {
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    if (-not (($user -split ';') -contains $dir)) { [Environment]::SetEnvironmentVariable('Path', "$dir;$user", 'User') }
    if (-not (($env:Path -split ';') -contains $dir)) { $env:Path = "$dir;$env:Path" }
}
AddUserPath (Join-Path $env:USERPROFILE '.local\bin')   # where uv and Claude Code install themselves
if (Test-Path (Join-Path $Base 'git\cmd')) { AddUserPath (Join-Path $Base 'git\cmd') }

$steps = [ordered]@{
    git    = {
        if (Has git) { return }
        $zip = Fetch git
        Expand-Archive -Path $zip -DestinationPath (Join-Path $Base 'git') -Force
        Remove-Item $zip -Force
        AddUserPath (Join-Path $Base 'git\cmd')
    }
    uv     = {
        if (Has uv) { return }
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        if (-not (Has uv)) { throw 'uv não ficou disponível' }
    }
    core   = {
        if (-not (Test-Path (Join-Path $Core '.git'))) {
            Run git @('clone', '--quiet', $Repo, $Core)
            Run git @('-C', $Core, 'remote', 'rename', 'origin', 'upstream')   # `aos update` reads releases from upstream
        }
        $target = if ($Ref) { "upstream/$Ref" } else { (& git -C $Core tag --list 'v*' --sort=-v:refname | Select-Object -First 1) }
        if ($Ref) { Run git @('-C', $Core, 'fetch', '--quiet', 'upstream', $Ref) }
        if ($target) { Run git @('-C', $Core, 'checkout', '--quiet', '-B', 'main', $target) }
    }
    claude = {
        if (Has claude) { return }
        Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
        if (-not (Has claude)) { throw 'Claude Code não ficou disponível' }
    }
    paseo  = {
        $exe = Join-Path $env:LOCALAPPDATA 'Programs\Paseo\Paseo.exe'
        if (Test-Path $exe) { return }
        $setup = Fetch paseo
        $p = Start-Process -FilePath $setup -ArgumentList '/S', '/currentuser' -Wait -PassThru
        Remove-Item $setup -Force
        Log "paseo setup exit $($p.ExitCode)"
        if (-not (Test-Path $exe)) { throw "o instalador do Paseo terminou sem instalar (código $($p.ExitCode))" }
    }
    setup  = {
        Push-Location $Core
        try { Run uv @('sync', '--locked', '--quiet'); Run uv @('run', 'aos', 'setup') } finally { Pop-Location }
    }
    page   = {
        # the page runs in the background from logon (pythonw: no console window); a desktop shortcut opens it
        $pyw = Join-Path $Core '.venv\Scripts\pythonw.exe'
        $a = New-ScheduledTaskAction -Execute $pyw -Argument '-m assistantos page' -WorkingDirectory $Core
        $t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
        $s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -StartWhenAvailable
        Register-ScheduledTask -TaskName 'assistantOS-pagina' -Action $a -Trigger $t -Settings $s -Force | Out-Null
        Start-ScheduledTask -TaskName 'assistantOS-pagina'
        $url = Join-Path ([Environment]::GetFolderPath('Desktop')) 'assistantOS.url'
        Set-Content -Path $url -Encoding ASCII -Value "[InternetShortcut]`r`nURL=http://127.0.0.1:8422/"
    }
}

foreach ($name in $Step) {
    try { Log "== $name"; & $steps[$name]; Log "== $name ok" }
    catch { Log "== $name FALHOU: $_"; Write-Output "FALHOU em '$name': $_"; exit 1 }
}
exit 0
