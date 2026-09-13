; ============================================================================
; StudySync — instalador Windows (Inno Setup 6)
;
; Gerado por desktop\release.ps1, que passa a versão:
;   ISCC.exe /DAppVersion=1.0.0 desktop\installer.iss
;
; Instalação por usuário (sem pedir administrador) em
; %LOCALAPPDATA%\Programs\StudySync. Os dados do app ficam em outra pasta
; (%LOCALAPPDATA%\StudySync) e NÃO são apagados ao desinstalar ou atualizar.
; ============================================================================

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
; Nunca mude o AppId: é por ele que o Windows reconhece uma atualização.
AppId={{09A103C3-C417-46D1-8ABF-1C8BAB514C72}
AppName=StudySync
AppVersion={#AppVersion}
AppVerName=StudySync {#AppVersion}
AppPublisher=Kaue Christian
AppPublisherURL=https://github.com/KaueChristian/StudySync
AppSupportURL=https://github.com/KaueChristian/StudySync/issues
VersionInfoVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\StudySync
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
; `x64` (e não `x64compatible`, de 6.3+) para compilar também em Inno Setup 6.0–6.2.
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; Mesmo nome do mutex de instância única do launcher: pede para fechar o app
; antes de atualizar/desinstalar.
AppMutex=StudySync.Desktop
LicenseFile=..\LICENSE
OutputDir=release
OutputBaseFilename=StudySync-Setup-{#AppVersion}
UninstallDisplayIcon={app}\StudySync.exe
UninstallDisplayName=StudySync
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\StudySync\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; Atualização: remove os arquivos da versão anterior (dependências podem ter
; mudado de nome) antes de copiar os novos. Só a pasta do programa.
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{autoprograms}\StudySync"; Filename: "{app}\StudySync.exe"
Name: "{autodesktop}\StudySync"; Filename: "{app}\StudySync.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\StudySync.exe"; Description: "{cm:LaunchProgram,StudySync}"; Flags: nowait postinstall skipifsilent
