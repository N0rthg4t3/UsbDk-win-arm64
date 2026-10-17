# UsbDk for Windows on ARM64 (experimental)

This is an **experimental** fork of [daynix/UsbDk](https://github.com/daynix/UsbDk)
that builds natively for Windows 10/11 on ARM64 (Snapdragon X and similar).
It has not been tested broadly, so don't rely on it in production.

UsbDk (USB Development Kit) is an open-source library for Windows. It gives
user-mode applications direct, exclusive access to USB devices: it detaches the
device from the Windows PnP manager and its drivers, and gives user mode an API
for USB operations on it. It handles all types of USB devices, bulk and
isochronous transfers, and composite devices.

The stock x64 UsbDk installs under emulation on ARM64 Windows, but its driver
can never load there. That makes the x64 UsbDk unusable for software that bundles
it on ARM64 machines, such as Shadow PC's USB forwarding.

## What changed for ARM64

* The solution and all projects have `Win10 Debug`, `Win10 Debug_NoSign` and
  `Win10 Release` configurations for the `ARM64` platform. They are generated
  from the x64 ones by `Tools/add_arm64.py`; re-run it after merging upstream
  project changes. ARM64 Windows starts at Windows 10 1709, so only `Win10`
  configurations exist.
* The ARM64 builds target KMDF 1.15 instead of 1.11, because current WDKs have
  no KMDF 1.11 headers, and no 1.11 libraries for ARM64. Every ARM64 Windows
  release ships a newer KMDF inbox.
* Microsoft never shipped a WDF co-installer for ARM64, so `UsbDkHelper` skips it
  on ARM64 builds (`USBDK_USE_WDF_COINSTALLER` in `UsbDkHelper/WdfCoinstaller.h`).
* The installer now refuses a package built for a different CPU than the OS, for
  example the x64 package running under emulation on ARM64. Before this, it
  installed a driver that could never start.
* The sources build cleanly (warnings are errors) with VS 2022 and WDK 26100:
  two anonymous `using X = struct : Base` aliases became named structs (C5208),
  the deprecated `ExAllocatePoolWithTag` warning is silenced in the driver
  (C4996), and an unused parameter in `UsbDkInstaller` is now used (C4100).
* Removed: the upstream AppVeyor CI, the VS2015-only multi-OS build scripts, the
  x86/x64-only WiX MSI installer, and support documents written for the upstream
  maintainers. They are still in the git history.

The x86/x64 configurations are still in the projects but are not maintained in
this fork.

## Building

**Tools required:**

* Visual Studio 2022 or Build Tools 2022, with these components:
  * MSVC ARM64 build tools (`Microsoft.VisualStudio.Component.VC.Tools.ARM64`)
  * MSVC ARM64 Spectre-mitigated libraries
    (`Microsoft.VisualStudio.Component.VC.Runtimes.ARM64.Spectre`)
  * Windows 11 SDK 10.0.26100
    (`Microsoft.VisualStudio.Component.Windows11SDK.26100`)
  * Windows Driver Kit: `Component.Microsoft.Windows.DriverKit` for Visual
    Studio, or `Component.Microsoft.Windows.DriverKit.BuildTools` for Build Tools
* WDK 10.0.26100 (`winget install Microsoft.WindowsWDK.10.0.26100`)

**Compilation:**

```bat
buildArm64.bat Release
buildArm64.bat Debug
```

On an ARM64 machine the script always uses the native ARM64 MSBuild and
compiler, even when it is started from an emulated x64 shell. The emulated
32-bit compiler runs out of address space for precompiled headers (errors C3859
and C1076).

Keep the source tree at a short path, such as `C:\src\UsbDk`. Deep paths go
over the 260-character limit for MSBuild's intermediate files (error MSB6003).

You can also open `UsbDk.sln` and pick a `Win10 *|ARM64` configuration.
Release output goes to `Install\ARM64\Win10Release\` and Debug output goes to
`Install_Debug\ARM64\Win10Debug\`. The installable files are in the
`UsbDk_Package` subfolder. `UsbDk.sys` is signed with a WDK test certificate
that the build creates on first use.

## Installing and running

A self-built driver loads only when test signing is enabled:

1. Turn off Secure Boot in the firmware setup.
2. In an elevated prompt, run `bcdedit /set testsigning on`, then reboot.
3. In an elevated prompt, go to the `UsbDk_Package` folder and run
   `UsbDkController.exe -i`.

Run `UsbDkController.exe` without parameters to see the other options. To
uninstall, run `UsbDkController.exe -u`, then `bcdedit /set testsigning off`,
and turn Secure Boot back on.

To load the driver with Secure Boot left on, it must be signed through the
Microsoft Hardware Dev Center (attestation signing).

## Documentation

* `ARCHITECTURE` in the source tree root
* `Documentation/` for driver signing, tracing and the device hider
* `UsbDkHelper/UsbDkHelper.h` and `UsbDkHelper/UsbDkHelperHider.h` for the API

## License

Apache License 2.0, see `LICENSE`. UsbDk was originally written by Red Hat and
Daynix Computing.
