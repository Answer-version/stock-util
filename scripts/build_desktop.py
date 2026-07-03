from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
SPEC_PATH = ROOT / "desktop_app.spec"


def build(clean: bool) -> None:
    if clean:
        shutil.rmtree(DIST_DIR, ignore_errors=True)
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        str(SPEC_PATH),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    _package_artifacts()


def _package_artifacts() -> None:
    artifact_dir = DIST_DIR / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "darwin":
        app_bundle = DIST_DIR / "QuantVibe.app"
        if app_bundle.exists():
            dmg_path = artifact_dir / "QuantVibe-macOS.dmg"
            if dmg_path.exists():
                dmg_path.unlink()
            subprocess.run(
                [
                    "hdiutil",
                    "create",
                    "-volname",
                    "QuantVibe",
                    "-srcfolder",
                    str(app_bundle),
                    "-ov",
                    "-format",
                    "UDZO",
                    str(dmg_path),
                ],
                check=True,
            )
    else:
        bundle_dir = DIST_DIR / "QuantVibe"
        if bundle_dir.exists():
            archive_base = artifact_dir / "QuantVibe-Windows"
            shutil.make_archive(str(archive_base), "zip", root_dir=DIST_DIR, base_dir="QuantVibe")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build QuantVibe desktop app")
    parser.add_argument("--clean", action="store_true", help="remove previous build artifacts before packaging")
    args = parser.parse_args()
    build(clean=args.clean)


if __name__ == "__main__":
    main()
