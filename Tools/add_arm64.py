"""Add ARM64 platform configurations to the UsbDk solution and projects.

ARM64 Windows exists only as Windows 10 1709+ / Windows 11, so only the
"Win10 *" configurations are cloned from their x64 counterparts.
Idempotent: does nothing for a file that already has ARM64 configurations.

Usage: add_arm64.py [source tree root]   (default: the root of this tree)
"""
import re
import sys
from pathlib import Path

CONFIGS = ("Win10 Debug", "Win10 Debug_NoSign", "Win10 Release")
DRIVER_PROJECT = "UsbDk/UsbDk.vcxproj"
USER_MODE_PROJECTS = [
    "UsbDkHelper/UsbDkHelper.vcxproj",
    "UsbDkController/UsbDkController.vcxproj",
    "UsbDkInstHelper/UsbDkInstHelper.vcxproj",
]
PROJECTS = [DRIVER_PROJECT] + USER_MODE_PROJECTS + ["UsbDk Package/UsbDk Package.vcxproj"]

# Overrides for the user mode projects, inserted just before Microsoft.Cpp.targets
USER_MODE_ARM64_OVERRIDES = [
    "  <PropertyGroup Condition=\"'$(Platform)'=='ARM64'\">",
    "    <!-- WDK ARM64 props always enable LTCG, which cannot be combined with incremental linking -->",
    "    <LinkIncremental>false</LinkIncremental>",
    "  </PropertyGroup>",
    "  <ItemDefinitionGroup Condition=\"'$(Platform)'=='ARM64'\">",
    "    <ClCompile>",
    "      <!-- WDK ARM64 props disable C++ exceptions, UsbDk user mode code relies on them -->",
    "      <ExceptionHandling>Sync</ExceptionHandling>",
    "    </ClCompile>",
    "  </ItemDefinitionGroup>",
]
CPP_TARGETS_IMPORT = '  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />'
TARGET_VERSION_WIN7 = "    <TargetVersion>Windows7</TargetVersion>"
TARGET_VERSION_ARM64 = "    <TargetVersion Condition=\"'$(Platform)'=='ARM64'\">Windows10</TargetVersion>"


def to_arm64(text):
    text = re.sub(r"\|x64(['\"])", r"|ARM64\1", text)
    text = text.replace("<Platform>x64</Platform>", "<Platform>ARM64</Platform>")
    text = text.replace("_AMD64_=1", "_ARM64_=1").replace("_AMD64_", "_ARM64_")
    text = re.sub(r"(?<=[;>])AMD64(?=;)", "ARM64", text)
    # KMDF 1.11 has no ARM64 libraries and current WDKs no 1.11 headers at all;
    # every ARM64 Windows release ships KMDF >= 1.23 inbox.
    text = text.replace("<KMDF_VERSION_MINOR>11</KMDF_VERSION_MINOR>",
                        "<KMDF_VERSION_MINOR>15</KMDF_VERSION_MINOR>")
    text = text.replace("KMDF_VERSION_MINOR=11", "KMDF_VERSION_MINOR=15")
    text = text.replace("\\Include\\wdf\\kmdf\\1.11", "\\Include\\wdf\\kmdf\\1.15")
    return text


def is_target(line):
    return any(f"{c}|x64'" in line or f'{c}|x64"' in line for c in CONFIGS)


def read_text(path):
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    return text, bom, newline


def write_text(path, text, bom):
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))


def add_user_mode_overrides(lines):
    out = []
    for line in lines:
        if line == CPP_TARGETS_IMPORT:
            out.extend(USER_MODE_ARM64_OVERRIDES)
        out.append(line)
        if line == TARGET_VERSION_WIN7:
            out.append(TARGET_VERSION_ARM64)
    return out


def process_project(root, name):
    path = root / name
    text, bom, newline = read_text(path)
    if "|ARM64" in text:
        print(f"skip (already has ARM64): {path}")
        return
    lines = text.split(newline)
    out, i, added = [], 0, 0
    while i < len(lines):
        line = lines[i]
        if not is_target(line):
            out.append(line)
            i += 1
            continue
        tag = re.match(r"\s*<([\w.]+)", line).group(1)
        indent = line[: len(line) - len(line.lstrip())]
        end = i
        if not (line.rstrip().endswith("/>") or f"</{tag}>" in line):
            while lines[end] != f"{indent}</{tag}>":
                end += 1
        block = lines[i : end + 1]
        out.extend(block)
        out.extend(to_arm64(l) for l in block)
        added += 1
        i = end + 1
    if name in USER_MODE_PROJECTS:
        out = add_user_mode_overrides(out)
    write_text(path, newline.join(out), bom)
    print(f"{path}: cloned {added} x64 blocks to ARM64")


def process_solution(root):
    path = root / "UsbDk.sln"
    text, bom, newline = read_text(path)
    if "|ARM64" in text:
        print(f"skip (already has ARM64): {path}")
        return
    out = []
    for line in text.split(newline):
        out.append(line)
        if any(f"{c}|x64" in line for c in CONFIGS):
            out.append(line.replace("|x64", "|ARM64"))
    write_text(path, newline.join(out), bom)
    print(f"{path}: added ARM64 solution configurations")


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    process_solution(root)
    for p in PROJECTS:
        process_project(root, p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
