; assistantOS-Setup.exe — the Windows installer a customer double-clicks. Built by .github/workflows/installer.yml
; (Inno Setup 6 on GitHub's Windows runner). Per user: no admin rights, no UAC prompt. All the work is bootstrap.ps1,
; run one step at a time so the wizard shows what it is doing; this file is only the wizard around it.
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{8046732A-8FB5-4379-9890-ABB450B75EB3}
AppName=assistantOS
AppVersion={#AppVersion}
AppPublisher=assistantOS
AppPublisherURL=https://igallina.github.io/assistantOS/
DefaultDirName={localappdata}\assistantOS
PrivilegesRequired=lowest
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
ArchitecturesAllowed=x64compatible or arm64
ArchitecturesInstallIn64BitMode=x64compatible or arm64
OutputDir=..\dist
OutputBaseFilename=assistantOS-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=assistantOS

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Messages]
pt.WelcomeLabel2=Vamos instalar o assistantOS e o que ele precisa: Git, Python (uv), Claude Code e Paseo.%n%nLeva de 5 a 15 minutos e não pede senha de administrador. Deixe o computador ligado e conectado à internet.

[Files]
Source: "bootstrap.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Run]
Filename: "http://127.0.0.1:8422/"; Description: "Abrir o assistantOS"; Flags: postinstall shellexec nowait skipifsilent

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -Command ""Unregister-ScheduledTask -TaskName assistantOS-pagina,assistantOS -Confirm:$false -ErrorAction SilentlyContinue"""; Flags: runhidden; RunOnceId: "tasks"

[Code]
const
  StepCount = 7;
var
  Failed: Boolean;

function StepName(I: Integer): String;
begin
  case I of
    0: Result := 'git'; 1: Result := 'uv'; 2: Result := 'core'; 3: Result := 'claude';
    4: Result := 'paseo'; 5: Result := 'setup'; 6: Result := 'page';
  end;
end;

function StepLabel(I: Integer): String;
begin
  case I of
    0: Result := 'Instalando o Git...';
    1: Result := 'Instalando o Python (uv)...';
    2: Result := 'Baixando o assistantOS...';
    3: Result := 'Instalando o Claude Code...';
    4: Result := 'Instalando o Paseo (pode levar alguns minutos)...';
    5: Result := 'Configurando o assistente (pode levar alguns minutos)...';
    6: Result := 'Preparando a página...';
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  I, Code: Integer;
begin
  if CurStep <> ssPostInstall then Exit;
  WizardForm.ProgressGauge.Min := 0;
  WizardForm.ProgressGauge.Max := StepCount;
  for I := 0 to StepCount - 1 do
  begin
    WizardForm.StatusLabel.Caption := StepLabel(I);
    WizardForm.ProgressGauge.Position := I;
    WizardForm.Refresh;
    if not Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\bootstrap.ps1') +
                '" -Step ' + StepName(I), '', SW_HIDE, ewWaitUntilTerminated, Code) or (Code <> 0) then
    begin
      Failed := True;
      MsgBox('A instalação parou em: ' + StepLabel(I) + #13#10#13#10 +
             'Rode o instalador de novo: ele continua de onde parou.' + #13#10 +
             'Se parar de novo, envie este arquivo para quem instalou com você:' + #13#10 +
             ExpandConstant('{localappdata}\assistantOS\install.log'), mbError, MB_OK);
      Exit;
    end;
  end;
  WizardForm.ProgressGauge.Position := StepCount;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpFinished) and Failed then
  begin
    WizardForm.FinishedLabel.Caption := 'A instalação não terminou. Rode o instalador de novo: ele continua de onde parou.';
    WizardForm.RunList.Visible := False;
  end;
end;
