#!/usr/bin/env python
from __future__ import annotations

import json
import math
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

import imageio.v3 as iio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont, ImageOps
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = REPO_ROOT / "data" / "benchmark_assets"
PREVIEW_ROOT = BENCH_ROOT / "previews"
MANIFEST_PATH = BENCH_ROOT / "preview_manifest.json"
CATALOG_JSON_PATH = BENCH_ROOT / "benchmark_asset_catalog.json"
CATALOG_MD_PATH = BENCH_ROOT / "benchmark_asset_catalog.md"
INVENTORY_MD_PATH = BENCH_ROOT / "upstream_repo_inventory.md"
README_PATH = BENCH_ROOT / "README.md"

AUTOBIO_ROOT = Path("/mnt/d/xwh/ailab记录/工作/26年04月/robot/AutoBio/autobio")
LABUTOPIA_LOCAL_ROOT = BENCH_ROOT / "files" / "labutopia"
LABUTOPIA_REPO = "Rui-li023/LabUtopia"

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
SCENE_WIDTH = 360
SCENE_HEIGHT = 240


def slugify(text: str) -> str:
    text = text.lower().replace("/", "_")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "item"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def rel_from_bench(path: Path) -> str:
    return path.relative_to(BENCH_ROOT).as_posix()


def path_cell(paths: list[str] | str) -> str:
    if isinstance(paths, str):
        return f"`{paths}`"
    return "<br>".join(f"`{item}`" for item in paths)


def image_cell(path: str | None, alt: str) -> str:
    if not path:
        return ""
    return f'<img src="{path}" width="160" alt="{alt}">'


def media_url(path: str) -> str:
    return f"https://media.githubusercontent.com/media/{LABUTOPIA_REPO}/main/{quote(path)}"


def http_get_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "LabOS preview renderer"})
    with urlopen(request) as response:
        return response.read()


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def add_label(image: Image.Image, title: str, subtitle: str | None = None) -> Image.Image:
    image = image.convert("RGBA")
    draw = ImageDraw.Draw(image)
    title_font = load_font(20)
    subtitle_font = load_font(14)
    margin = 12
    lines = wrap_text(draw, title, title_font, image.width - margin * 2)
    subtitle_lines = wrap_text(draw, subtitle, subtitle_font, image.width - margin * 2) if subtitle else []
    box_height = 12 + len(lines) * 24 + (len(subtitle_lines) * 18 if subtitle_lines else 0) + 8
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle((0, image.height - box_height, image.width, image.height), fill=(10, 18, 28, 180))
    y = image.height - box_height + 8
    for line in lines:
        overlay_draw.text((margin, y), line, font=title_font, fill=(255, 255, 255, 255))
        y += 24
    for line in subtitle_lines:
        overlay_draw.text((margin, y), line, font=subtitle_font, fill=(220, 228, 238, 255))
        y += 18
    return Image.alpha_composite(image, overlay).convert("RGB")


def placeholder_image(title: str, subtitle: str) -> Image.Image:
    image = Image.new("RGB", (SCENE_WIDTH, SCENE_HEIGHT), color=(236, 240, 244))
    draw = ImageDraw.Draw(image)
    title_font = load_font(22)
    subtitle_font = load_font(16)
    title_lines = wrap_text(draw, title, title_font, image.width - 32)
    subtitle_lines = wrap_text(draw, subtitle, subtitle_font, image.width - 32)
    total_height = len(title_lines) * 28 + len(subtitle_lines) * 20
    y = (image.height - total_height) // 2
    for line in title_lines:
        box = draw.textbbox((0, 0), line, font=title_font)
        x = (image.width - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=title_font, fill=(30, 41, 59))
        y += 28
    for line in subtitle_lines:
        box = draw.textbbox((0, 0), line, font=subtitle_font)
        x = (image.width - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=subtitle_font, fill=(71, 85, 105))
        y += 20
    return image


def save_image(image: Image.Image, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    image.save(out_path)


def corner_background_color(image: Image.Image, sample: int = 16) -> np.ndarray:
    rgb = image.convert("RGB")
    arr = np.asarray(rgb)
    h, w = arr.shape[:2]
    sample = max(1, min(sample, h // 4 or 1, w // 4 or 1))
    patches = [
        arr[:sample, :sample],
        arr[:sample, w - sample :],
        arr[h - sample :, :sample],
        arr[h - sample :, w - sample :],
    ]
    pixels = np.concatenate([patch.reshape(-1, 3) for patch in patches], axis=0)
    return np.median(pixels, axis=0)


def resize_with_aspect_padding(
    image: Image.Image,
    out_size: tuple[int, int],
    background: tuple[int, int, int],
) -> Image.Image:
    target_w, target_h = out_size
    target_ratio = target_w / target_h
    current_ratio = image.width / image.height
    if current_ratio < target_ratio:
        padded_w = max(target_w, int(round(image.height * target_ratio)))
        padded_h = image.height
    else:
        padded_w = image.width
        padded_h = max(target_h, int(round(image.width / target_ratio)))
    canvas = Image.new("RGB", (padded_w, padded_h), background)
    offset = ((padded_w - image.width) // 2, (padded_h - image.height) // 2)
    canvas.paste(image, offset)
    return canvas.resize(out_size, Image.LANCZOS)


def crop_to_content(
    image: Image.Image,
    out_size: tuple[int, int],
    diff_threshold: int = 16,
    padding_ratio: float = 0.18,
) -> Image.Image:
    rgb = image.convert("RGB")
    arr = np.asarray(rgb)
    bg = corner_background_color(rgb)
    diff = np.abs(arr.astype(np.int16) - bg.astype(np.int16)).max(axis=2)
    mask = diff > diff_threshold
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return resize_with_aspect_padding(rgb, out_size, tuple(int(x) for x in bg))
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    width = x1 - x0 + 1
    height = y1 - y0 + 1
    image_w, image_h = rgb.size
    coverage = (width * height) / (image_w * image_h)
    if coverage >= 0.92:
        return resize_with_aspect_padding(rgb, out_size, tuple(int(x) for x in bg))
    pad_x = max(int(round(width * padding_ratio)), 12)
    pad_y = max(int(round(height * padding_ratio)), 12)
    left = max(0, x0 - pad_x)
    top = max(0, y0 - pad_y)
    right = min(image_w, x1 + pad_x + 1)
    bottom = min(image_h, y1 + pad_y + 1)
    cropped = rgb.crop((left, top, right, bottom))
    return resize_with_aspect_padding(cropped, out_size, tuple(int(x) for x in bg))


def render_mjcf_preview(xml_path: Path, out_path: Path, title: str, distance_scale: float = 2.8) -> None:
    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = model.stat.center
    extent = max(float(model.stat.extent), 0.2)
    camera.distance = extent * distance_scale
    camera.azimuth = 145
    camera.elevation = -22
    renderer = mujoco.Renderer(model, SCENE_WIDTH, SCENE_HEIGHT)
    try:
        renderer.update_scene(data, camera=camera)
        image = renderer.render()
    finally:
        renderer.close()
    pil_image = crop_to_content(Image.fromarray(image).convert("RGB"), (SCENE_WIDTH, SCENE_HEIGHT))
    pil_image = ImageOps.autocontrast(pil_image, cutoff=1)
    save_image(add_label(pil_image, title), out_path)


def load_mesh_list(source: Path) -> list[trimesh.Trimesh]:
    candidates: list[Path] = []
    if source.is_file():
        candidates = [source]
    elif source.is_dir():
        all_meshes = [
            path
            for path in source.rglob("*")
            if path.is_file() and path.suffix.lower() in {".obj", ".stl"}
        ]
        preferred = [
            path
            for path in all_meshes
            if "visual" in path.stem.lower()
            and "collision" not in path.stem.lower()
            and "inertia" not in path.stem.lower()
        ]
        if preferred:
            candidates = preferred
        else:
            candidates = [
                path
                for path in all_meshes
                if "collision" not in path.stem.lower()
                and "inertia" not in path.stem.lower()
            ]
        if not candidates:
            candidates = all_meshes
    meshes: list[trimesh.Trimesh] = []
    for candidate in candidates:
        try:
            loaded = trimesh.load(candidate, force="mesh", process=False)
        except Exception:
            continue
        if isinstance(loaded, trimesh.Trimesh) and len(loaded.vertices) and len(loaded.faces):
            meshes.append(loaded)
    return meshes


def render_mesh_preview(source: Path, out_path: Path, title: str) -> None:
    meshes = load_mesh_list(source)
    if not meshes:
        save_image(placeholder_image(title, "Preview unavailable"), out_path)
        return
    mesh = trimesh.util.concatenate(meshes)
    vertices = mesh.vertices.copy()
    faces = mesh.faces
    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    center = (mins + maxs) / 2.0
    scale = float(np.max(maxs - mins))
    if scale <= 0:
        scale = 1.0
    vertices = (vertices - center) / scale

    fig = plt.figure(figsize=(4.0, 3.0), dpi=140)
    ax = fig.add_subplot(111, projection="3d")
    tri_vertices = vertices[faces]
    collection = Poly3DCollection(
        tri_vertices,
        facecolor=(0.34, 0.47, 0.62, 1.0),
        edgecolor=(0.10, 0.14, 0.20, 0.45),
        linewidth=0.18,
    )
    ax.add_collection3d(collection)
    span = 0.62
    ax.set_xlim(-span, span)
    ax.set_ylim(-span, span)
    ax.set_zlim(-span, span)
    ax.view_init(elev=24, azim=42)
    ax.set_box_aspect((1, 1, 1))
    ax.axis("off")
    fig.patch.set_facecolor("#f5f7fa")
    ax.set_facecolor("#f5f7fa")
    fig.subplots_adjust(0, 0, 1, 1)
    ax.set_position([0, 0, 1, 1])
    ensure_dir(out_path.parent)
    tmp_path = out_path.with_suffix(".raw.png")
    fig.savefig(tmp_path, bbox_inches="tight", pad_inches=0.02, facecolor="#f5f7fa")
    plt.close(fig)
    raw = Image.open(tmp_path).convert("RGB")
    raw = crop_to_content(raw, (SCENE_WIDTH, SCENE_HEIGHT), diff_threshold=10, padding_ratio=0.12)
    raw = ImageOps.autocontrast(raw, cutoff=1)
    tmp_path.unlink(missing_ok=True)
    save_image(add_label(raw, title), out_path)


def write_preview(source_path: Path, out_path: Path, title: str, preview_kind: str) -> None:
    try:
        if preview_kind == "mjcf":
            render_mjcf_preview(source_path, out_path, title)
        else:
            render_mesh_preview(source_path, out_path, title)
    except Exception as exc:
        save_image(placeholder_image(title, f"{type(exc).__name__}: preview unavailable"), out_path)


def local_labutopia_thumb(scene_path: str) -> Path | None:
    candidate = LABUTOPIA_LOCAL_ROOT / scene_path
    thumb = candidate.parent / ".thumbs" / "256x256" / f"{candidate.name}.png"
    if thumb.exists():
        return thumb
    return None


def load_labutopia_thumb(scene_path: str) -> Image.Image:
    thumb = local_labutopia_thumb(scene_path)
    if thumb and thumb.exists():
        return Image.open(thumb).convert("RGB")
    remote_path = f"{Path(scene_path).parent.as_posix()}/.thumbs/256x256/{Path(scene_path).name}.png"
    try:
        return Image.open(BytesIO(http_get_bytes(media_url(remote_path)))).convert("RGB")
    except Exception:
        return placeholder_image(Path(scene_path).name, "No scene thumbnail available")


def save_labutopia_scene_preview(scene_path: str, out_path: Path, title: str, subtitle: str | None = None) -> None:
    image = load_labutopia_thumb(scene_path).resize((SCENE_WIDTH, SCENE_HEIGHT), Image.LANCZOS)
    save_image(add_label(image, title, subtitle), out_path)


@dataclass
class TableRow:
    columns: list[str]


def make_table(headers: list[str], rows: list[TableRow]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        cells = [cell.replace("|", r"\|") for cell in row.columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def autobio_scene_rows() -> list[dict[str, str]]:
    scene_paths = sorted((AUTOBIO_ROOT / "model" / "scene").glob("*.xml"))
    rows = []
    for path in scene_paths:
        rows.append(
            {
                "name": path.stem,
                "path": f"autobio/model/scene/{path.name}",
                "source": str(path),
                "slug": slugify(path.stem),
            }
        )
    return rows


def autobio_composite_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    object_base = AUTOBIO_ROOT / "model" / "object"
    object_families: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(object_base.glob("*.xml")):
        family = path.stem.removesuffix(".gen")
        object_families[family].append(path)

    for family in sorted(object_families):
        family_paths = sorted(
            object_families[family],
            key=lambda item: (item.stem.endswith(".gen"), item.name),
        )
        primary = next((item for item in family_paths if not item.stem.endswith(".gen")), family_paths[0])
        rows.append(
            {
                "category": "object",
                "name": family,
                "key": f"autobio/model/object/{family}",
                "display_paths": [f"autobio/model/object/{path.name}" for path in family_paths],
                "source": str(primary),
                "slug": slugify(f"object-{family}"),
            }
        )

    def collect(subdir: str, category: str) -> None:
        base = AUTOBIO_ROOT / "model" / subdir
        for path in sorted(base.glob("*.xml")):
            rows.append(
                {
                    "category": category,
                    "name": path.stem,
                    "key": f"autobio/model/{subdir}/{path.name}",
                    "display_paths": [f"autobio/model/{subdir}/{path.name}"],
                    "source": str(path),
                    "slug": slugify(f"{category}-{path.stem}"),
                }
            )

    collect("instrument", "instrument")
    collect("robot", "robot")
    collect("hand", "hand")
    return rows


def autobio_standalone_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    raw_sources = [
        ("cell_dish_100_vis", "autobio/assets/container/cell_dish_100_vis.obj"),
        ("centrifuge_1-5ml_screw_vis", "autobio/assets/container/centrifuge_1-5ml_screw_vis"),
        ("centrifuge_10ml_vis", "autobio/assets/container/centrifuge_10ml_vis.obj"),
        ("centrifuge_1500ul_no_lid_vis", "autobio/assets/container/centrifuge_1500ul_no_lid_vis.obj"),
        ("centrifuge_15ml_screw_vis", "autobio/assets/container/centrifuge_15ml_screw_vis"),
        ("centrifuge_50ml_vis", "autobio/assets/container/centrifuge_50ml_vis.obj"),
        ("centrifuge_50ml_screw_vis", "autobio/assets/container/centrifuge_50ml_screw_vis"),
        ("cryovial_1-8ml_vis", "autobio/assets/container/cryovial_1-8ml_vis"),
        ("pcr_plate_96well_vis", "autobio/assets/container/pcr_plate_96well_vis.obj"),
        ("tip_200ul_vis", "autobio/assets/container/tip_200ul_vis"),
        ("centrifuge_10slot_vis", "autobio/assets/rack/centrifuge_10slot_vis.obj"),
        ("centrifuge_plate_60well_vis", "autobio/assets/rack/centrifuge_plate_60well_vis.obj"),
        ("pipette_rack_tri_vis", "autobio/assets/rack/pipette_rack_tri_vis.obj"),
        ("tip_box_24slot_vis", "autobio/assets/rack/tip_box_24slot_vis.obj"),
        ("pipette", "autobio/assets/tool/pipette"),
        ("centrifuge_eppendorf_5430", "autobio/assets/instrument/centrifuge_eppendorf_5430"),
        ("centrifuge_eppendorf_5910_ri", "autobio/assets/instrument/centrifuge_eppendorf_5910_ri"),
        ("centrifuge_tiangen_tgear_mini", "autobio/assets/instrument/centrifuge_tiangen_tgear_mini"),
        ("thermal_cycler_biorad_c1000", "autobio/assets/instrument/thermal_cycler_biorad_c1000"),
        ("thermal_mixer_eppendorf_c", "autobio/assets/instrument/thermal_mixer_eppendorf_c"),
        ("vortex_mixer_genie_2", "autobio/assets/instrument/vortex_mixer_genie_2"),
        ("aloha2", "autobio/assets/robot/aloha2"),
        ("dexhand021", "autobio/assets/robot/dexhand021"),
        ("robotiq", "autobio/assets/robot/robotiq"),
        ("ur5e", "autobio/assets/robot/ur5e"),
    ]
    for name, rel_path in raw_sources:
        rows.append(
            {
                "name": name,
                "display_path": rel_path,
                "source": str(AUTOBIO_ROOT / rel_path.replace("autobio/", "")),
                "slug": slugify(name),
            }
        )
    return rows


LAB_SCENES = [
    ("chemistry main scene", "lab_001", "assets/chemistry_lab/lab_001/lab_001.usd"),
    ("chemistry main scene", "lab_003", "assets/chemistry_lab/lab_003/lab_003.usd"),
    ("chemistry main scene", "Scene1_hard", "assets/chemistry_lab/hard_task/Scene1_hard.usd"),
    ("chemistry special scene", "clock", "assets/chemistry_lab/lab_003/clock.usd"),
    ("navigation scene", "navigation_lab_01", "assets/navigation_lab/navigation_lab_01/lab.usd"),
]

LAB_SCENE_NAME_TO_PATH = {scene_name: scene_path for _scene_type, scene_name, scene_path in LAB_SCENES}

LAB_CHEM_USD = [
    ("main scene", "assets/chemistry_lab/lab_001/lab_001.usd", "lab_001"),
    ("main scene", "assets/chemistry_lab/lab_003/lab_003.usd", "lab_003"),
    ("main scene", "assets/chemistry_lab/hard_task/Scene1_hard.usd", "Scene1_hard"),
    ("special scene", "assets/chemistry_lab/lab_003/clock.usd", "clock"),
    ("auxiliary USD", "assets/chemistry_lab/hard_task/lab_004.usd", "lab_004"),
    ("SubUSD", "assets/chemistry_lab/hard_task/SubUSDs/lab_015.usd", "Scene1_hard"),
    ("SubUSD", "assets/chemistry_lab/lab_003/SubUSDs/lab_015.usd", "lab_003"),
]

LAB_SCENE_OBJECTS = [
    ("cabinet", ["/World/Cabinet_01", "/World/Cabinet_02"], "assets/chemistry_lab/lab_001/lab_001.usd"),
    ("drying box", ["/World/DryingBox_01", "/World/DryingBox_02", "/World/DryingBox_03"], "assets/chemistry_lab/lab_001/lab_001.usd"),
    ("button", ["/World/DryingBox_01/button", "/World/heat_device/button"], "assets/chemistry_lab/lab_001/lab_001.usd"),
    ("beaker", ["/World/beaker1", "/World/beaker2", "/World/beaker3", "/World/beaker_2", "/World/target_beaker"], "assets/chemistry_lab/lab_001/lab_001.usd"),
    ("conical bottle", ["/World/conical_bottle02", "/World/conical_bottle03", "/World/conical_bottle04"], "assets/chemistry_lab/lab_001/lab_001.usd"),
    ("glass rod", ["/World/glass_rod"], "assets/chemistry_lab/lab_003/lab_003.usd"),
    ("graduated cylinder", ["/World/graduated_cylinder_03"], "assets/chemistry_lab/lab_001/lab_001.usd"),
    ("heat device", ["/World/heat_device"], "assets/chemistry_lab/lab_003/lab_003.usd"),
    ("muffle furnace", ["/World/MuffleFurnace"], "assets/chemistry_lab/hard_task/Scene1_hard.usd"),
    ("rack / platform", ["/World/target_plat"], "assets/chemistry_lab/hard_task/Scene1_hard.usd"),
    ("table surface", ["/World/table/surface", "/World/table/surface/mesh"], "assets/chemistry_lab/lab_003/lab_003.usd"),
]


def build_preview_manifest() -> dict[str, dict[str, str]]:
    manifest: dict[str, dict[str, str]] = {
        "autobio_scenes": {},
        "autobio_composite": {},
        "autobio_standalone": {},
        "labutopia_scenes": {},
        "labutopia_chem_usd": {},
        "labutopia_scene_objects": {},
        "catalog_entry": {},
    }

    for row in autobio_scene_rows():
        out_path = PREVIEW_ROOT / "autobio" / "scenes" / f"{row['slug']}.png"
        write_preview(Path(row["source"]), out_path, row["name"], "mjcf")
        manifest["autobio_scenes"][row["path"]] = rel_from_bench(out_path)

    for row in autobio_composite_rows():
        out_path = PREVIEW_ROOT / "autobio" / "composite" / f"{row['slug']}.png"
        write_preview(Path(row["source"]), out_path, row["name"], "mjcf")
        manifest["autobio_composite"][row["key"]] = rel_from_bench(out_path)

    for row in autobio_standalone_rows():
        out_path = PREVIEW_ROOT / "autobio" / "standalone" / f"{row['slug']}.png"
        write_preview(Path(row["source"]), out_path, row["name"], "mesh")
        manifest["autobio_standalone"][row["display_path"]] = rel_from_bench(out_path)

    for scene_type, scene_name, scene_path in LAB_SCENES:
        out_path = PREVIEW_ROOT / "labutopia" / "scenes" / f"{slugify(scene_name)}.png"
        save_labutopia_scene_preview(scene_path, out_path, scene_name, scene_type)
        manifest["labutopia_scenes"][scene_path] = rel_from_bench(out_path)

    for classification, scene_path, substitute in LAB_CHEM_USD:
        render_scene_path = scene_path
        if not local_labutopia_thumb(scene_path):
            render_scene_path = LAB_SCENE_NAME_TO_PATH.get(substitute, scene_path)
        title = Path(scene_path).stem
        subtitle = classification
        if classification == "SubUSD":
            subtitle = f"{classification} from {Path(render_scene_path).stem}"
        out_path = PREVIEW_ROOT / "labutopia" / "chem_usd" / f"{slugify(scene_path)}.png"
        save_labutopia_scene_preview(render_scene_path, out_path, title, subtitle)
        manifest["labutopia_chem_usd"][scene_path] = rel_from_bench(out_path)

    for family, object_paths, scene_path in LAB_SCENE_OBJECTS:
        out_path = PREVIEW_ROOT / "labutopia" / "scene_objects" / f"{slugify(family)}.png"
        subtitle = object_paths[0] if len(object_paths) == 1 else f"{object_paths[0]} ..."
        save_labutopia_scene_preview(scene_path, out_path, family, subtitle)
        manifest["labutopia_scene_objects"][family] = rel_from_bench(out_path)

    entries = json.loads(CATALOG_JSON_PATH.read_text(encoding="utf-8"))
    for entry in entries:
        if entry["source_project"] == "labutopia":
            scene_path = entry["local_relative_path"].split("/files/labutopia/", 1)[1].split("#", 1)[0]
            out_path = PREVIEW_ROOT / "labutopia" / "catalog" / f"{slugify(entry['asset_id'])}.png"
            label = entry["local_relative_path"].split("#", 1)[1]
            save_labutopia_scene_preview(scene_path, out_path, entry["asset_name"], label)
        else:
            out_path = PREVIEW_ROOT / "autobio" / "catalog" / f"{slugify(entry['asset_id'])}.png"
            source = REPO_ROOT / entry["local_relative_path"]
            kind = "mjcf" if entry["reference_kind"] == "package_entrypoint" else "mesh"
            write_preview(source, out_path, entry["asset_name"], kind)
        manifest["catalog_entry"][entry["asset_id"]] = rel_from_bench(out_path)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def write_catalog_markdown(manifest: dict[str, dict[str, str]]) -> None:
    entries = json.loads(CATALOG_JSON_PATH.read_text(encoding="utf-8"))
    lines = [
        "# Benchmark 核心资产清单",
        "",
        "| Preview | Asset Name | Match Group | Entry Type | Source Project | Local Relative Path | Render Status | Original URL |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for entry in entries:
        preview = image_cell(manifest["catalog_entry"].get(entry["asset_id"]), entry["asset_name"])
        lines.append(
            "| "
            + " | ".join(
                [
                    preview,
                    entry["asset_name"],
                    entry["match_group"],
                    {
                        "standalone_mesh_root": "asset (standalone_mesh_root)",
                        "package_entrypoint": "composite asset (package_entrypoint)",
                        "scene_prim_reference": "scene object reference (scene_prim_reference)",
                    }[entry["reference_kind"]],
                    entry["source_project"],
                    f"`{entry['local_relative_path']}`",
                    entry["render_status"],
                    f"[link]({entry['original_url']})",
                ]
            )
            + " |"
        )
    lines.append("")
    CATALOG_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_inventory_markdown(manifest: dict[str, dict[str, str]]) -> None:
    auto_scene_rows = [
        TableRow(
            [
                image_cell(manifest["autobio_scenes"].get(row["path"]), row["name"]),
                row["name"],
                path_cell(row["path"]),
            ]
        )
        for row in autobio_scene_rows()
    ]

    auto_composite_rows = [
        TableRow(
            [
                image_cell(manifest["autobio_composite"].get(row["key"]), row["name"]),
                row["category"],
                row["name"],
                path_cell(row["display_paths"]),
            ]
        )
        for row in autobio_composite_rows()
    ]

    auto_standalone_rows = [
        TableRow(
            [
                image_cell(manifest["autobio_standalone"].get(row["display_path"]), row["name"]),
                row["name"],
                path_cell(row["display_path"]),
            ]
        )
        for row in autobio_standalone_rows()
    ]

    lab_scene_rows = [
        TableRow(
            [
                image_cell(manifest["labutopia_scenes"].get(scene_path), scene_name),
                scene_type,
                scene_name,
                path_cell(scene_path),
            ]
        )
        for scene_type, scene_name, scene_path in LAB_SCENES
    ]

    lab_chem_rows = [
        TableRow(
            [
                image_cell(manifest["labutopia_chem_usd"].get(scene_path), scene_path),
                classification,
                path_cell(scene_path),
            ]
        )
        for classification, scene_path, substitute in LAB_CHEM_USD
    ]

    lab_object_rows = [
        TableRow(
            [
                image_cell(manifest["labutopia_scene_objects"].get(family), family),
                family,
                path_cell(object_paths),
            ]
        )
        for family, object_paths, _scene_path in LAB_SCENE_OBJECTS
    ]

    entries = json.loads(CATALOG_JSON_PATH.read_text(encoding="utf-8"))
    lab_catalog_rows = [
        TableRow(
            [
                image_cell(manifest["catalog_entry"].get(entry["asset_id"]), entry["asset_name"]),
                entry["asset_name"],
                path_cell(entry["local_relative_path"].split("/files/labutopia/", 1)[1]),
            ]
        )
        for entry in entries
        if entry["source_project"] == "labutopia"
    ]

    lines = [
        "# AutoBio / LabUtopia 上游结构清单",
        "",
        "这份文档只做两件事：",
        "",
        "1. 把 `AutoBio` 和 `LabUtopia` 里的 `scene / asset / composite asset / scene object reference` 分清楚",
        "2. 给出每一类的实际路径和预览图",
        "",
        "## 1. 先记住四个概念",
        "",
        "| 术语 | 中文解释 | 典型例子 |",
        "|---|---|---|",
        "| `scene` | 整个实验环境入口，打开后看到的是整张实验台或整个实验室 | `autobio/model/scene/lab.xml`、`assets/chemistry_lab/lab_001/lab_001.usd` |",
        "| `asset (standalone_mesh_root)` | 单个对象的独立 mesh 根入口 | `autobio/assets/container/pcr_plate_96well_vis.obj` |",
        "| `composite asset (package_entrypoint)` | 单个对象的装配入口文件，会继续引用多个 mesh / 部件 | `autobio/model/instrument/centrifuge_eppendorf_5430.xml` |",
        "| `scene object reference (scene_prim_reference)` | scene 里的某个对象路径，本身不是独立文件 | `assets/chemistry_lab/lab_001/lab_001.usd#/World/conical_bottle02` |",
        "",
        "一眼判断规则：",
        "",
        "1. 加载后如果出来的是完整环境，就是 `scene`",
        "2. 如果长得像 `xxx.usd#/World/...`，就是 `scene object reference`",
        "3. 如果它是单对象 mesh 根文件，就是 `asset`",
        "4. 如果它是单对象入口文件，但会继续引用很多部件，就是 `composite asset`",
        "",
        "## 2. AutoBio",
        "",
        "- 组织方式：`asset-first + scene xml`",
        "- `scene` 主入口：`autobio/model/scene/`",
        "- `composite asset` 主入口：`autobio/model/object/`、`autobio/model/instrument/`、`autobio/model/robot/`、`autobio/model/hand/`",
        "- `asset` / raw mesh 主入口：`autobio/assets/container/`、`autobio/assets/rack/`、`autobio/assets/tool/`、`autobio/assets/instrument/`、`autobio/assets/robot/`",
        "",
        "### 2.1 AutoBio scenes",
        "",
        make_table(["Preview", "Scene", "Path"], auto_scene_rows),
        "",
        "### 2.2 AutoBio composite assets",
        "",
        "说明：`object/` 目录里若同时存在 `.xml` 与 `.gen.xml`，这里按同一资产 family 合并展示。",
        "",
        make_table(["Preview", "Category", "Name", "Path"], auto_composite_rows),
        "",
        "### 2.3 AutoBio standalone assets / raw mesh roots",
        "",
        make_table(["Preview", "Name", "Path"], auto_standalone_rows),
        "",
        "## 3. LabUtopia",
        "",
        "- 组织方式：`scene-first USD`",
        "- 主入口是 `scene`，不是对象级独立 mesh",
        "- 当前 benchmark 里使用的主要是 `scene object reference`",
        "- 下面的对象预览图目前使用的是“scene 缩略图 + 对象标签”，因为当前还没有把这些对象从 USD scene 里独立抽取出来",
        "",
        "### 3.1 LabUtopia scenes",
        "",
        make_table(["Preview", "Type", "Scene", "Path"], lab_scene_rows),
        "",
        "### 3.2 Chemistry USD files visible in the repo",
        "",
        make_table(["Preview", "Classification", "Path"], lab_chem_rows),
        "",
        "### 3.3 LabUtopia scene object families",
        "",
        make_table(["Representative Preview", "Family", "Scene Object Paths"], lab_object_rows),
        "",
        "### 3.4 LabUtopia benchmark scene object entries",
        "",
        make_table(["Preview", "Name", "Path"], lab_catalog_rows),
        "",
        "### 3.5 LabUtopia support files",
        "",
        "| Type | Count |",
        "|---|---:|",
        "| `.usd` | 7 |",
        "| `.mdl` | 260 |",
        "| `.jpg` | 75 |",
        "| `.png` | 28 |",
        "",
        "这些 `materials / textures / SubUSDs` 是 support files，不应该直接算作独立实验资产。",
        "",
        "## 4. 当前 benchmark 主清单和仓库全量结构的关系",
        "",
        "- `AutoBio` 当前 benchmark 主清单：`14 x asset + 7 x composite asset`",
        "- `LabUtopia` 当前 benchmark 主清单：`8 x scene object reference`",
        "- 这些数字都只是 benchmark 现在实际使用的条目，不是两个仓库的全量资产数",
        "",
    ]
    INVENTORY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def update_readme() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    text = text.replace("repo_asset_scene_inventory.md", "upstream_repo_inventory.md")
    text = text.replace("merged_asset_catalog.md", "benchmark_asset_catalog.md")
    text = text.replace("merged_asset_catalog.json", "benchmark_asset_catalog.json")
    if "- `previews/`" not in text:
        text = text.replace(
            "- `upstream_repo_inventory.md`\n  - 两个仓库的完整分类清单，带预览图\n",
            "- `upstream_repo_inventory.md`\n  - 两个仓库的完整分类清单，带预览图\n- `previews/`\n  - 脚本生成的 scene / asset 预览图\n",
        )
    README_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    if PREVIEW_ROOT.exists():
        shutil.rmtree(PREVIEW_ROOT)
    ensure_dir(PREVIEW_ROOT)
    manifest = build_preview_manifest()
    write_catalog_markdown(manifest)
    write_inventory_markdown(manifest)
    update_readme()
    print(json.dumps({"preview_manifest": rel_from_bench(MANIFEST_PATH)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
