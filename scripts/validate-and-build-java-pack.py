#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"
OUT = DIST / "EnderNation-Resource-Pack.zip"
PNG_SIG = b"\x89PNG\r\n\x1a\n"

errors: list[str] = []
warnings: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"Invalid JSON: {path.relative_to(ROOT)}: {exc}")
        return None


def resource_path(identifier: str, default_ns: str, kind: str, extension: str) -> Path:
    if ":" in identifier:
        ns, rel = identifier.split(":", 1)
    else:
        ns, rel = default_ns, identifier
    return ASSETS / ns / kind / f"{rel}{extension}"


# Required Java pack root.
for required in (ROOT / "pack.mcmeta", ROOT / "pack.png", ASSETS):
    if not required.exists():
        fail(f"Missing required pack entry: {required.relative_to(ROOT)}")

# pack.mcmeta compatibility contract.
mcmeta = load_json(ROOT / "pack.mcmeta")
if isinstance(mcmeta, dict):
    pack = mcmeta.get("pack", {})
    if pack.get("min_format") != 75:
        fail(f"pack.mcmeta min_format must be 75, found {pack.get('min_format')!r}")
    if pack.get("max_format") != [97, 1]:
        fail(f"pack.mcmeta max_format must be [97, 1], found {pack.get('max_format')!r}")

# Every Java JSON must parse.
json_files = sorted(ASSETS.rglob("*.json"))
parsed: dict[Path, object] = {}
for path in json_files:
    data = load_json(path)
    if data is not None:
        parsed[path] = data

# Every Java PNG must have a valid PNG signature.
png_files = [ROOT / "pack.png", *sorted(ASSETS.rglob("*.png"))]
for path in png_files:
    try:
        if path.read_bytes()[:8] != PNG_SIG:
            fail(f"Bad PNG signature: {path.relative_to(ROOT)}")
    except Exception as exc:
        fail(f"Cannot read PNG: {path.relative_to(ROOT)}: {exc}")

# Font bitmap providers must point to actual textures.
font_provider_count = 0
for path, data in parsed.items():
    rel = path.relative_to(ASSETS)
    parts = rel.parts
    if len(parts) < 3 or parts[1] != "font" or not isinstance(data, dict):
        continue
    namespace = parts[0]
    providers = data.get("providers")
    if not isinstance(providers, list):
        continue
    for idx, provider in enumerate(providers):
        if not isinstance(provider, dict):
            continue
        if provider.get("type") == "bitmap":
            font_provider_count += 1
            file_id = provider.get("file")
            if not isinstance(file_id, str):
                fail(f"Bitmap provider without file: {path.relative_to(ROOT)} provider #{idx}")
                continue
            if ":" in file_id:
                ns, tex = file_id.split(":", 1)
            else:
                ns, tex = namespace, file_id
            target = ASSETS / ns / "textures" / tex
            if not target.exists():
                fail(
                    f"Missing bitmap texture: {path.relative_to(ROOT)} provider #{idx}: "
                    f"{file_id} -> {target.relative_to(ROOT)}"
                )

# sounds.json references in their own namespace must resolve to .ogg files.
sound_ref_count = 0
for path, data in parsed.items():
    if path.name != "sounds.json" or not isinstance(data, dict):
        continue
    namespace = path.relative_to(ASSETS).parts[0]
    for event, definition in data.items():
        if not isinstance(definition, dict):
            continue
        sounds = definition.get("sounds", [])
        if not isinstance(sounds, list):
            continue
        for entry in sounds:
            name = entry if isinstance(entry, str) else entry.get("name") if isinstance(entry, dict) else None
            if not isinstance(name, str):
                continue
            sound_ref_count += 1
            if ":" in name:
                ns, rel = name.split(":", 1)
            else:
                ns, rel = namespace, name
            if ns != namespace:
                continue
            target = ASSETS / ns / "sounds" / f"{rel}.ogg"
            if not target.exists():
                fail(
                    f"Missing sound file: {path.relative_to(ROOT)} event {event!r}: "
                    f"{name} -> {target.relative_to(ROOT)}"
                )

# Validate custom model references and detect obvious namespace mistakes.
model_ref_count = 0
for path, data in parsed.items():
    rel = path.relative_to(ASSETS)
    parts = rel.parts
    if len(parts) < 3 or parts[1] not in {"models", "items"}:
        continue
    namespace = parts[0]

    def walk(value, key_path=()):
        global model_ref_count
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, (*key_path, k))
            return
        if isinstance(value, list):
            for i, v in enumerate(value):
                walk(v, (*key_path, i))
            return
        if not isinstance(value, str):
            return

        last = key_path[-1] if key_path else None

        if last == "parent" and ":" in value:
            ns, model = value.split(":", 1)
            if ns != "minecraft":
                model_ref_count += 1
                target = ASSETS / ns / "models" / f"{model}.json"
                if not target.exists():
                    fail(
                        f"Missing parent model: {path.relative_to(ROOT)}: "
                        f"{value} -> {target.relative_to(ROOT)}"
                    )

        # Texture values occur below a 'textures' object in Java models.
        if "textures" in key_path and not value.startswith("#"):
            model_ref_count += 1
            if ":" in value:
                ns, tex = value.split(":", 1)
            else:
                ns, tex = namespace, value
            target = ASSETS / ns / "textures" / f"{tex}.png"

            if ns != "minecraft" and not target.exists():
                fail(
                    f"Missing custom texture: {path.relative_to(ROOT)}: "
                    f"{value} -> {target.relative_to(ROOT)}"
                )

            # If a custom model explicitly points at a missing minecraft texture,
            # but the identical texture exists in the model's own namespace,
            # it is almost certainly a stale namespace reference.
            if (
                namespace != "minecraft"
                and ns == "minecraft"
                and not target.exists()
            ):
                same_namespace = ASSETS / namespace / "textures" / f"{tex}.png"
                if same_namespace.exists():
                    fail(
                        f"Texture namespace mismatch: {path.relative_to(ROOT)} uses {value}, "
                        f"but {same_namespace.relative_to(ROOT)} exists"
                    )

        # New item-definition model IDs.
        if last == "model" and ":" in value and value != "minecraft:model":
            ns, model = value.split(":", 1)
            if ns != "minecraft":
                model_ref_count += 1
                target = ASSETS / ns / "models" / f"{model}.json"
                if not target.exists():
                    fail(
                        f"Missing item model: {path.relative_to(ROOT)}: "
                        f"{value} -> {target.relative_to(ROOT)}"
                    )

    walk(data)

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print(f"ERROR: {error}")
    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")
    sys.exit(1)

# Build a deterministic Java pack ZIP.
DIST.mkdir(exist_ok=True)
if OUT.exists():
    OUT.unlink()

pack_files = [ROOT / "pack.mcmeta", ROOT / "pack.png"]
pack_files.extend(p for p in ASSETS.rglob("*") if p.is_file())
pack_files = sorted(pack_files, key=lambda p: p.relative_to(ROOT).as_posix())

with zipfile.ZipFile(
    OUT,
    "w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
    strict_timestamps=True,
) as zf:
    for path in pack_files:
        arcname = path.relative_to(ROOT).as_posix()
        info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        data = path.read_bytes()
        zf.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

# Verify ZIP root and content set exactly match the intended Java pack.
with zipfile.ZipFile(OUT, "r") as zf:
    names = zf.namelist()
    if "pack.mcmeta" not in names or "pack.png" not in names:
        fail("Built ZIP is missing pack.mcmeta or pack.png at ZIP root")
    if any(not (n in {"pack.mcmeta", "pack.png"} or n.startswith("assets/")) for n in names):
        fail("Built ZIP contains files outside pack.mcmeta, pack.png, assets/")
    expected = {p.relative_to(ROOT).as_posix() for p in pack_files}
    if set(names) != expected:
        fail("Built ZIP file list does not exactly match Java pack source set")

if errors:
    print("POST-BUILD VALIDATION FAILED")
    for error in errors:
        print(f"ERROR: {error}")
    sys.exit(1)

blob = OUT.read_bytes()
sha1 = hashlib.sha1(blob).hexdigest()
sha256 = hashlib.sha256(blob).hexdigest()
(DIST / "EnderNation-Resource-Pack.zip.sha1").write_text(f"{sha1}  EnderNation-Resource-Pack.zip\n", encoding="ascii")
(DIST / "EnderNation-Resource-Pack.zip.sha256").write_text(f"{sha256}  EnderNation-Resource-Pack.zip\n", encoding="ascii")

print("VALIDATION OK")
print(f"JSON files: {len(json_files)}")
print(f"PNG files: {len(png_files)}")
print(f"Bitmap font providers: {font_provider_count}")
print(f"Sound references: {sound_ref_count}")
print(f"Custom model references checked: {model_ref_count}")
print(f"ZIP files: {len(pack_files)}")
print(f"ZIP bytes: {len(blob)}")
print(f"SHA1={sha1}")
print(f"SHA256={sha256}")
