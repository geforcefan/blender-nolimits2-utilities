import argparse
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile

repository_root = pathlib.Path(__file__).resolve().parents[2]
module_directory = repository_root / "blender" / "nolimits2"
extension_directory = repository_root / "blender" / "nolimits2_utilities"

platform_by_wheel_tag = {
    ("macosx", "arm64"): "macos-arm64",
    ("macosx", "x86_64"): "macos-x64",
    ("win", "amd64"): "windows-x64",
    ("win", "arm64"): "windows-arm64",
    ("manylinux", "x86_64"): "linux-x64",
    ("manylinux", "aarch64"): "linux-arm64",
}


def platform_of(wheel):
    for (system, architecture), platform in platform_by_wheel_tag.items():
        if system in wheel.name and architecture in wheel.name:
            return platform
    raise SystemExit(f"unknown platform for wheel {wheel.name}")


def built_wheels(directory):
    if sys.version_info < (3, 12):
        raise SystemExit(f"run this with CPython 3.12 or newer, this is {platform.python_version()}")
    environment = dict(os.environ, MACOSX_DEPLOYMENT_TARGET="11.0")
    subprocess.run([sys.executable, "-m", "pip", "wheel", str(module_directory),
                    "--no-deps", "--no-cache-dir", "--wheel-dir", str(directory)], check=True, env=environment)
    return sorted(pathlib.Path(directory).glob("*.whl"))


def write_manifest(wheels, platforms):
    manifest = extension_directory / "blender_manifest.toml"
    lines = []
    for line in manifest.read_text().splitlines():
        if line.startswith("wheels = "):
            line = "wheels = [" + ", ".join(f'"./wheels/{wheel.name}"' for wheel in wheels) + "]"
        elif line.startswith("platforms = "):
            line = "platforms = [" + ", ".join(f'"{platform}"' for platform in platforms) + "]"
        lines.append(line)
    manifest.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheels", help="directory with prebuilt wheels, one per platform")
    parser.add_argument("--output", default=str(repository_root / "build" / "blender"))
    parser.add_argument("--blender", default="blender")
    arguments = parser.parse_args()

    with tempfile.TemporaryDirectory() as scratch:
        wheels = sorted(pathlib.Path(arguments.wheels).rglob("*.whl")) if arguments.wheels else built_wheels(scratch)
        if not wheels:
            raise SystemExit("no wheels to pack")
        wheel_directory = extension_directory / "wheels"
        shutil.rmtree(wheel_directory, ignore_errors=True)
        wheel_directory.mkdir(parents=True)
        for wheel in wheels:
            shutil.copy(wheel, wheel_directory / wheel.name)
        write_manifest(wheels, sorted({platform_of(wheel) for wheel in wheels}))

    output = pathlib.Path(arguments.output)
    output.mkdir(parents=True, exist_ok=True)
    for stale in output.glob("nolimits2_utilities-*.zip"):
        stale.unlink()
    subprocess.run([arguments.blender, "--command", "extension", "build",
                    "--source-dir", str(extension_directory), "--output-dir", str(output)], check=True)


main()
