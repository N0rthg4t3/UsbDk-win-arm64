@echo off
rem Build UsbDk for Windows 10/11 ARM64.
rem Usage: buildArm64.bat [Release|Debug|Debug_NoSign]   (default: Release)
rem Output: Install\ARM64\Win10<cfg>\  (Debug variants: Install_Debug\ARM64\...)

SETLOCAL EnableExtensions

set CFG=%1
if [%CFG%] EQU [] set CFG=Release

set VSWHERE="%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
for /f "usebackq tokens=*" %%a in (`%VSWHERE% -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.ARM64 -find MSBuild\**\Bin\MSBuild.exe`) do set MSBUILD=%%a

if not defined MSBUILD (
  echo MSBuild with ARM64 C++ tools not found
  exit /B 1
)

rem On an ARM64 host use the native MSBuild and compiler even if this script runs
rem in an emulated x64/x86 shell. The emulated 32-bit compiler picked otherwise
rem runs out of address space for precompiled headers (C3859/C1076).
for /f "tokens=3" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PROCESSOR_ARCHITECTURE 2^>nul') do set HOST_ARCH=%%a
if /I [%HOST_ARCH%] EQU [ARM64] (
  for %%m in ("%MSBUILD%") do if exist "%%~dpmarm64\MSBuild.exe" set MSBUILD=%%~dpmarm64\MSBuild.exe
  set PROCESSOR_ARCHITECTURE=ARM64
  set PreferredToolArchitecture=arm64
)

"%MSBUILD%" "%~dp0UsbDk.sln" /m /t:Rebuild "/p:Configuration=Win10 %CFG%" /p:Platform=ARM64 /fl /flp:logfile=%~dp0buildArm64_%CFG%.log;verbosity=normal
if %ERRORLEVEL% NEQ 0 exit /B 1

ENDLOCAL
