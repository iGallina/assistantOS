# assistantOS — everything the Windows installer does, for the current user only (no admin, no UAC prompt).
# Run by the Inno Setup wizard (install/assistantOS.iss) one step at a time; also runnable by hand:
#   powershell -NoProfile -ExecutionPolicy Bypass -File bootstrap.ps1 [-Step git,uv,core,claude,hermes,setup,perfil,page] [-Ref main]
# Every step is idempotent: running it again skips what is already in place. Log: %LOCALAPPDATA%\assistantOS\install.log
# Downloads are pinned and checked against each project's published SHA-256; uv and Claude Code use their official
# installers, as install.ps1 always did, and so does Hermes. Files fetched here carry no "downloaded from the internet"
# mark, so SmartScreen never stops them.
param(
    [string[]]$Step = @('git', 'uv', 'core', 'claude', 'hermes', 'setup', 'perfil', 'page'),
    [string]$Ref = ''   # a branch or tag to install instead of the newest release (testing only)
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
# Started from PowerShell 7 (CI, or an owner who has it), Windows PowerShell inherits 7's PSModulePath and fails to load
# its own modules ("Get-ExecutionPolicy ... could not be loaded"). Reset it to 5.1's defaults; child processes inherit this.
$env:PSModulePath = @((Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'WindowsPowerShell\Modules'),
    (Join-Path $env:ProgramFiles 'WindowsPowerShell\Modules'), (Join-Path $env:SystemRoot 'system32\WindowsPowerShell\v1.0\Modules')) -join ';'
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
function RunInstaller([string]$url, [string[]]$extra = @()) {
    # official install scripts run in their own process: an `exit` inside them can't end this one, and their output is logged
    $f = Join-Path $env:TEMP ('aos-' + [guid]::NewGuid().ToString('N') + '.ps1')
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $f
    try { Run 'powershell.exe' (@('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $f) + $extra) } finally { Remove-Item $f -Force -ErrorAction SilentlyContinue }
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
        RunInstaller 'https://astral.sh/uv/install.ps1'
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
        RunInstaller 'https://claude.ai/install.ps1'
        if (-not (Has claude)) { throw 'Claude Code não ficou disponível' }
    }
    hermes = {
        if (Has hermes) { return }
        # Hermes' official per-user installer (no admin): CLI, gateway and the desktop app with its shortcuts. The browser
        # and computer-use tools stay off; the owner can add them later with `hermes pm install`.
        RunInstaller 'https://hermes-agent.nousresearch.com/install.ps1' @('-NonInteractive', '-IncludeDesktop', '-SkipBrowser', '-SkipComputerUse')
        $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:Path   # Hermes adds itself to the user PATH
        if (-not (Has hermes)) { throw 'o Hermes não ficou disponível' }
    }
    setup  = {
        Push-Location $Core
        try { Run uv @('sync', '--locked', '--quiet'); Run uv @('run', 'aos', 'setup') } finally { Pop-Location }
    }
    perfil = {
        # the assistantOS distribution (skills, SOUL, MCP entry) as the owner's default Hermes profile
        $listed = (& hermes profile list 2>&1 | Out-String) -match '\bassistantos\b'
        if ($listed) { Run hermes @('profile', 'update', 'assistantos', '-y') }
        else { Run hermes @('profile', 'install', (Join-Path $Core 'hermes'), '-y') }
        $hhome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }
        $envFile = Join-Path $hhome 'profiles\assistantos\.env'
        if (-not (Test-Path (Split-Path $envFile))) { throw "perfil do Hermes não encontrado em $(Split-Path $envFile)" }
        # config.yaml's MCP entry reads ${AOS_HOME}: where assistantOS lives. UTF-8 without BOM, one line replaced.
        $lines = @(Get-Content $envFile -ErrorAction SilentlyContinue | Where-Object { $_ -notmatch '^AOS_HOME=' }) + "AOS_HOME=$Core"
        [IO.File]::WriteAllLines($envFile, [string[]]$lines, (New-Object Text.UTF8Encoding $false))
        Run hermes @('profile', 'use', 'assistantos')
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
