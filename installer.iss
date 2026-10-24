[Setup]
AppName=Raapid Language
AppVersion=0.0.1
DefaultDirName={autopf}\Raapid
DefaultGroupName=Raapid
OutputBaseFilename=raapid-0.0.1-setup
Compression=lzma
SolidCompression=yes
ChangesEnvironment=yes

[Files]
; Tells Inno Setup to grab the compiled app binary you built in Step 1
Source: "dist\raapid.exe"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
; This critical command auto-adds Raapid to the user's Command Prompt System PATH environment variables
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Flags: preservestringtype
