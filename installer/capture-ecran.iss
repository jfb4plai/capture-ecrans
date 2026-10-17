; Installateur de « Capture d'écran PLAI » (Inno Setup 6). Construit par le workflow GitHub :
;   iscc /DMyAppVersion=1.2.0 installer\capture-ecran.iss      (après PyInstaller : dist\Capture-ecran-PLAI\)
; Installation « pour l'utilisateur » : pas de droits administrateur. Réinstaller une version plus récente
; REMPLACE la précédente (même AppId) ; captures et réglages sont hors du dossier du programme et restent intacts.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppName "Capture d'écran PLAI"
#define MyExe "Capture-ecran-PLAI.exe"

[Setup]
AppId={{6F2B8D54-3C1E-4B7A-9E0D-5A1C7F4D2B91}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=jfb4plai
AppPublisherURL=https://jfb4plai.com/capture-ecran/
AppSupportURL=https://jfb4plai.com/capture-ecran/
VersionInfoVersion={#MyAppVersion}
DefaultDirName={autopf}\Capture-ecran-PLAI
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\installateur
OutputBaseFilename=Capture-ecran-PLAI-installateur
SetupIconFile=..\capture_ecran\assets\icon.ico
UninstallDisplayIcon={app}\{#MyExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=no
RestartApplications=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Un raccourci sur le &bureau"; GroupDescription: "Pour l'ouvrir facilement :"
Name: "autostart"; Description: "Lancer le programme à l'ouverture de &Windows (conseillé : les raccourcis clavier ne marchent que s'il tourne)"; GroupDescription: "Pour l'ouvrir facilement :"; Flags: unchecked

[Files]
Source: "..\dist\Capture-ecran-PLAI\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Mêmes noms de fichiers que ceux créés par le programme lui-même : ils remplacent les anciens raccourcis (pas de doublon).
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyExe}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyExe}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyExe}"; Parameters: "--reduit"; WorkingDir: "{app}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyExe}"; Description: "Lancer {#MyAppName} maintenant"; Flags: nowait postinstall skipifsilent

[Code]
procedure StopRunningApp();
var
  code: Integer;
begin
  // Un programme ouvert bloquerait le remplacement de ses fichiers. Rien n'est perdu : chaque capture est enregistrée au fur et à mesure.
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM {#MyExe}', '', SW_HIDE, ewWaitUntilTerminated, code);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  StopRunningApp();
  Result := '';
end;

function InitializeUninstall(): Boolean;
begin
  StopRunningApp();
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and not UninstallSilent() then
    MsgBox('Le programme est désinstallé.'#13#10#13#10 +
           'Vos captures (dossier « Capture-ecran-jfb4plai » du bureau) et vos réglages sont conservés.', mbInformation, MB_OK);
end;
