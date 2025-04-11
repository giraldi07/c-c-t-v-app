; setup.iss
[Setup]
AppName=CCTV Viewer Kota Bandung
AppVersion=1.0
DefaultDirName={pf}\CCTVViewer
DefaultGroupName=CCTV Viewer
OutputDir=output
OutputBaseFilename=CCTVViewer_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=icon.ico

[Files]
Source: "dist\CCTVViewer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "cctv_data.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\CCTV Viewer"; Filename: "{app}\CCTVViewer.exe"
Name: "{commondesktop}\CCTV Viewer"; Filename: "{app}\CCTVViewer.exe"