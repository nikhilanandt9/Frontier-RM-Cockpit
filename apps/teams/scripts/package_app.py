from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


TEAMS_ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = re.compile(r"\$\{\{([A-Z0-9_]+)}}")


def read_environment(name: str) -> dict[str, str]:
    path = TEAMS_ROOT / "env" / f".env.{name}"
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            raise ValueError(f"Invalid environment line: {raw_line}")
        values[key.strip()] = value.strip()
    return values


def resolve_manifest(environment: dict[str, str]) -> dict:
    source = (TEAMS_ROOT / "appPackage" / "manifest.json").read_text(encoding="utf-8")
    missing = sorted({name for name in PLACEHOLDER.findall(source) if not environment.get(name)})
    if missing:
        raise ValueError(f"Missing manifest variables: {', '.join(missing)}")
    resolved = PLACEHOLDER.sub(lambda match: environment[match.group(1)], source)
    manifest = json.loads(resolved)
    if manifest["manifestVersion"] != "1.26":
        raise ValueError("Teams manifest must use schema 1.26")
    if manifest["bots"][0]["scopes"] != ["personal"]:
        raise ValueError("Frontier RM demo bot must remain personal-scope only")
    return manifest


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path.name}")
    return struct.unpack(">II", header[16:24])


def build_package(environment_name: str, check_only: bool = False) -> Path | None:
    package_dir = TEAMS_ROOT / "appPackage"
    color = package_dir / "color.png"
    outline = package_dir / "outline.png"
    if png_dimensions(color) != (192, 192) or png_dimensions(outline) != (32, 32):
        raise ValueError("Teams icons do not have the required dimensions")
    manifest = resolve_manifest(read_environment(environment_name))
    if check_only:
        return None

    build_dir = package_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    resolved_manifest = build_dir / f"manifest.{environment_name}.json"
    resolved_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    output = build_dir / f"frontier-rm.{environment_name}.zip"
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
        archive.write(color, "color.png")
        archive.write(outline, "outline.png")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and package the Frontier RM Teams app")
    parser.add_argument("--env", default="playground", choices=["playground", "dev"])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = build_package(args.env, args.check)
    print("Teams package validation passed." if output is None else f"Created {output}")


if __name__ == "__main__":
    main()
