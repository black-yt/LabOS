#!/usr/bin/env python
from __future__ import annotations

import json
import math
import os
import re
import shutil
from collections import defaultdict
from contextlib import contextmanager
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
BENCH_ROOT = REPO_ROOT / "data" / "benchmark_inventory"
PREVIEW_ROOT = BENCH_ROOT / "previews"
MANIFEST_PATH = BENCH_ROOT / "preview_manifest.json"
CORE_INVENTORY_JSON_PATH = BENCH_ROOT / "benchmark_core_inventory.json"
README_PATH = BENCH_ROOT / "README.md"

AUTOBIO_ROOT = Path("/mnt/d/xwh/ailab记录/工作/26年04月/robot/AutoBio/autobio")
AUTOBIO_LOCAL_ROOT = BENCH_ROOT / "files" / "autobio" / "autobio"
AUTOBIO_PLUGIN_LIB = AUTOBIO_ROOT / "libmjlab.so.3.3.0"
LABUTOPIA_LOCAL_ROOT = BENCH_ROOT / "files" / "labutopia"
LABUTOPIA_REPO = "Rui-li023/LabUtopia"
_AUTOBIO_PLUGIN_LOADED = False

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


def load_autobio_plugin() -> None:
    global _AUTOBIO_PLUGIN_LOADED
    if _AUTOBIO_PLUGIN_LOADED or not AUTOBIO_PLUGIN_LIB.exists():
        return
    mujoco.mj_loadPluginLibrary(str(AUTOBIO_PLUGIN_LIB))
    _AUTOBIO_PLUGIN_LOADED = True


@contextmanager
def temporary_cwd(path: Path):
    original = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


def resolve_autobio_render_source(source: Path) -> Path:
    try:
        relative = source.relative_to(AUTOBIO_LOCAL_ROOT)
    except ValueError:
        return source
    return AUTOBIO_ROOT / relative


def is_autobio_render_source(source: Path) -> bool:
    try:
        source.relative_to(AUTOBIO_ROOT)
        return True
    except ValueError:
        return False


def path_cell(paths: list[str] | str) -> str:
    if isinstance(paths, str):
        return f"`{paths}`"
    return "<br>".join(f"`{item}`" for item in paths)


def image_cell(path: str | None, alt: str, width: int = 160) -> str:
    if not path:
        return ""
    return f'<img src="{path}" width="{width}" alt="{alt}">'


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


def reference_card(title: str, subtitle: str, detail: str | None = None) -> Image.Image:
    image = Image.new("RGB", (SCENE_WIDTH, SCENE_HEIGHT), color=(245, 247, 250))
    draw = ImageDraw.Draw(image)
    frame = (28, 28, image.width - 28, image.height - 84)
    draw.rounded_rectangle(frame, radius=16, outline=(148, 163, 184), width=2, fill=(255, 255, 255))
    draw.rounded_rectangle((52, 56, 136, 116), radius=10, outline=(59, 130, 246), width=2, fill=(239, 246, 255))
    draw.rounded_rectangle((184, 56, 268, 116), radius=10, outline=(16, 185, 129), width=2, fill=(236, 253, 245))
    draw.line((136, 86, 184, 86), fill=(100, 116, 139), width=3)
    draw.polygon([(176, 79), (176, 93), (186, 86)], fill=(100, 116, 139))
    icon_font = load_font(14)
    draw.text((68, 75), "XML", font=icon_font, fill=(30, 64, 175))
    draw.text((200, 75), "3D", font=icon_font, fill=(6, 95, 70))
    note_font = load_font(16)
    note = detail or "Use metadata card"
    note_lines = wrap_text(draw, note, note_font, image.width - 88)
    y = 132
    for line in note_lines[:2]:
        box = draw.textbbox((0, 0), line, font=note_font)
        x = (image.width - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=note_font, fill=(71, 85, 105))
        y += 20
    return add_label(image, title, subtitle)


def save_image(image: Image.Image, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    image.save(out_path)


def humanize_render_error(exc: Exception) -> str:
    message = str(exc)
    if "No such file or directory" in message:
        return "上游缺少 mesh 文件，使用结构卡片展示"
    if "mesh" in message and "not found" in message:
        return "上游 XML / mesh 引用异常，使用结构卡片展示"
    if "plugin" in message:
        return "上游插件依赖未满足，使用结构卡片展示"
    return "当前改用结构卡片展示"


AUTOBIO_PREVIEW_FALLBACKS = {
    "model/object/centrifuge_1-5ml.xml": (
        AUTOBIO_ROOT / "assets" / "container" / "centrifuge_1500ul_no_lid_vis.obj",
        "mesh",
        "使用相近的开放式 1.5 mL 管体预览",
    ),
    "model/object/centrifuge_15ml.xml": (
        AUTOBIO_ROOT / "assets" / "container" / "centrifuge_15ml_screw_vis",
        "mesh",
        "使用相近的 15 mL screw-cap 管体预览",
    ),
    "model/object/centrifuge_50ml_screw.xml": (
        AUTOBIO_ROOT / "assets" / "container" / "centrifuge_50ml_screw_vis",
        "mesh",
        "使用对应的 50 mL screw-cap mesh 预览",
    ),
}


def fallback_render_source(source_path: Path) -> tuple[Path, str, str] | None:
    resolved = resolve_autobio_render_source(source_path)
    try:
        relative = resolved.relative_to(AUTOBIO_ROOT).as_posix()
    except ValueError:
        return None
    return AUTOBIO_PREVIEW_FALLBACKS.get(relative)


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
    render_source = resolve_autobio_render_source(xml_path)
    if is_autobio_render_source(render_source):
        load_autobio_plugin()
        with temporary_cwd(AUTOBIO_ROOT):
            model = mujoco.MjModel.from_xml_path(str(render_source))
    else:
        model = mujoco.MjModel.from_xml_path(str(render_source))
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
        save_image(reference_card(title, "结构卡片", "未找到可渲染的 mesh 文件"), out_path)
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
        fallback = fallback_render_source(source_path)
        if fallback is not None:
            fallback_source, fallback_kind, fallback_reason = fallback
            try:
                if fallback_kind == "mjcf":
                    render_mjcf_preview(fallback_source, out_path, title)
                else:
                    render_mesh_preview(fallback_source, out_path, title)
                return
            except Exception:
                save_image(reference_card(title, "结构卡片", fallback_reason), out_path)
                return
        save_image(reference_card(title, "结构卡片", humanize_render_error(exc)), out_path)


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
            key=lambda item: (not item.stem.endswith(".gen"), item.name),
        )
        primary = next((item for item in family_paths if item.stem.endswith(".gen")), family_paths[0])
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


REFERENCE_KIND_LABELS = {
    "standalone_mesh_root": "独立对象",
    "package_entrypoint": "组合对象",
    "scene_prim_reference": "场景内对象引用",
}

SOURCE_LABELS = {
    "autobio": "AutoBio",
    "labutopia": "LabUtopia",
}

CATEGORY_LABELS = {
    "object": "对象",
    "instrument": "仪器",
    "robot": "机器人",
    "hand": "手部末端",
}

RENDER_STATUS_LABELS = {
    "ready_obj": "可直接按 mesh 渲染",
    "ready_mjcf_package": "可直接按 MJCF 装配渲染",
    "downloaded_usd_requires_conversion": "当前使用 USD 场景缩略图展示",
}


def load_core_entries() -> list[dict[str, Any]]:
    return json.loads(CORE_INVENTORY_JSON_PATH.read_text(encoding="utf-8"))


def render_status_label(status: str) -> str:
    return RENDER_STATUS_LABELS.get(status, status)


def source_label(source_project: str) -> str:
    return SOURCE_LABELS.get(source_project, source_project)


def relative_path_from_labutopia_local(local_relative_path: str) -> str:
    return local_relative_path.split("/files/labutopia/", 1)[1]


def extra_lab_scene_files() -> list[tuple[str, str, str]]:
    scene_paths = {scene_path for _scene_type, _scene_name, scene_path in LAB_SCENES}
    rows = []
    for classification, scene_path, substitute in LAB_CHEM_USD:
        if scene_path in scene_paths:
            continue
        rows.append((classification, scene_path, substitute))
    return rows


def build_preview_manifest() -> dict[str, dict[str, str]]:
    manifest: dict[str, dict[str, str]] = {
        "autobio_scenes": {},
        "autobio_composite": {},
        "autobio_standalone": {},
        "labutopia_scenes": {},
        "labutopia_chem_usd": {},
        "labutopia_scene_objects": {},
        "core_entries": {},
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

    for entry in load_core_entries():
        out_path = PREVIEW_ROOT / "core" / entry["source_project"] / f"{slugify(entry['entry_id'])}.png"
        if entry["source_project"] == "labutopia":
            scene_path = relative_path_from_labutopia_local(entry["local_relative_path"]).split("#", 1)[0]
            label = entry["local_relative_path"].split("#", 1)[1]
            save_labutopia_scene_preview(scene_path, out_path, entry["entry_name"], label)
        else:
            source = resolve_autobio_render_source(REPO_ROOT / entry["local_relative_path"])
            kind = "mjcf" if entry["reference_kind"] == "package_entrypoint" else "mesh"
            write_preview(source, out_path, entry["entry_name"], kind)
        manifest["core_entries"][entry["entry_id"]] = rel_from_bench(out_path)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def repo_overview_rows(entries: list[dict[str, Any]]) -> list[TableRow]:
    core_counts = defaultdict(int)
    for entry in entries:
        core_counts[entry["source_project"]] += 1

    return [
        TableRow(
            [
                "AutoBio",
                "对象优先，兼有完整 MuJoCo XML 场景",
                f"独立对象 {len(autobio_standalone_rows())}<br>组合对象 {len(autobio_composite_rows())}<br>完整场景 {len(autobio_scene_rows())}",
                str(core_counts["autobio"]),
                "`autobio/assets/`、`autobio/model/`",
            ]
        ),
        TableRow(
            [
                "LabUtopia",
                "场景优先，核心文件是 USD 场景",
                f"场景内对象引用 {len(LAB_SCENE_OBJECTS)}<br>完整场景 {len(LAB_SCENES)}<br>场景相关文件 {len(extra_lab_scene_files())}",
                str(core_counts["labutopia"]),
                "`assets/chemistry_lab/`",
            ]
        ),
    ]


def type_overview_rows() -> list[TableRow]:
    return [
        TableRow(
            [
                "`scene`",
                "完整场景入口，加载后看到的是整张实验台、整台设备或整个实验室。",
                "是",
                "`autobio/model/scene/lab.xml`<br>`assets/chemistry_lab/lab_001/lab_001.usd`",
            ]
        ),
        TableRow(
            [
                "`standalone_mesh_root`",
                "独立对象的 mesh 根入口，通常对应单个对象或单个对象目录。",
                "是",
                "`autobio/assets/container/pcr_plate_96well_vis.obj`",
            ]
        ),
        TableRow(
            [
                "`package_entrypoint`",
                "组合对象入口，会继续引用多个部件、材质或子文件。",
                "是",
                "`autobio/model/instrument/centrifuge_eppendorf_5430.xml`",
            ]
        ),
        TableRow(
            [
                "`scene_prim_reference`",
                "场景内对象引用，依附在某个 USD 场景里，本身不是独立文件。",
                "否",
                "`assets/chemistry_lab/lab_001/lab_001.usd#/World/conical_bottle02`",
            ]
        ),
    ]


def merged_scene_object_rows(manifest: dict[str, dict[str, str]]) -> list[TableRow]:
    rows = []
    for family, object_paths, scene_path in LAB_SCENE_OBJECTS:
        rows.append(
            TableRow(
                [
                    image_cell(manifest["labutopia_scene_objects"].get(family), family),
                    "LabUtopia",
                    family,
                    path_cell(object_paths),
                    f"`{scene_path}`",
                ]
            )
        )
    return rows


def merged_standalone_rows(manifest: dict[str, dict[str, str]]) -> list[TableRow]:
    rows = []
    for row in autobio_standalone_rows():
        rows.append(
            TableRow(
                [
                    image_cell(manifest["autobio_standalone"].get(row["display_path"]), row["name"]),
                    "AutoBio",
                    row["name"],
                    path_cell(row["display_path"]),
                ]
            )
        )
    return rows


def merged_composite_rows(manifest: dict[str, dict[str, str]]) -> list[TableRow]:
    rows = []
    for row in autobio_composite_rows():
        rows.append(
            TableRow(
                [
                    image_cell(manifest["autobio_composite"].get(row["key"]), row["name"]),
                    "AutoBio",
                    CATEGORY_LABELS.get(row["category"], row["category"]),
                    row["name"],
                    path_cell(row["display_paths"]),
                ]
            )
        )
    return rows


def merged_scene_rows(manifest: dict[str, dict[str, str]]) -> list[TableRow]:
    rows = []
    for row in autobio_scene_rows():
        rows.append(
            TableRow(
                [
                    image_cell(manifest["autobio_scenes"].get(row["path"]), row["name"]),
                    "AutoBio",
                    "完整场景",
                    row["name"],
                    path_cell(row["path"]),
                    "MuJoCo XML 场景入口",
                ]
            )
        )
    for scene_type, scene_name, scene_path in LAB_SCENES:
        rows.append(
            TableRow(
                [
                    image_cell(manifest["labutopia_scenes"].get(scene_path), scene_name),
                    "LabUtopia",
                    "完整场景",
                    scene_name,
                    path_cell(scene_path),
                    scene_type,
                ]
            )
        )
    for classification, scene_path, substitute in extra_lab_scene_files():
        rows.append(
            TableRow(
                [
                    image_cell(manifest["labutopia_chem_usd"].get(scene_path), scene_path),
                    "LabUtopia",
                    "场景相关文件",
                    Path(scene_path).stem,
                    path_cell(scene_path),
                    classification,
                ]
            )
        )
    return rows


def core_inventory_rows(
    manifest: dict[str, dict[str, str]],
    entries: list[dict[str, Any]],
) -> list[TableRow]:
    rows = []
    for entry in entries:
        rows.append(
            TableRow(
                [
                    image_cell(
                        manifest["core_entries"].get(entry["entry_id"]),
                        entry["entry_name"],
                        width=320,
                    ),
                    entry["entry_name"],
                    source_label(entry["source_project"]),
                    REFERENCE_KIND_LABELS[entry["reference_kind"]],
                    entry["match_group"],
                    "<br>".join(entry["aliases"]),
                    entry["purpose"],
                    f"`{entry['local_relative_path']}`",
                    render_status_label(entry["render_status"]),
                    f"[源文件]({entry['original_url']})",
                ]
            )
        )
    return rows


def write_readme(manifest: dict[str, dict[str, str]]) -> None:
    entries = load_core_entries()
    repo_rows = repo_overview_rows(entries)
    type_rows = type_overview_rows()
    scene_object_rows = merged_scene_object_rows(manifest)
    standalone_rows = merged_standalone_rows(manifest)
    composite_rows = merged_composite_rows(manifest)
    scene_rows = merged_scene_rows(manifest)
    core_rows = core_inventory_rows(manifest, entries)

    auto_core_count = sum(1 for entry in entries if entry["source_project"] == "autobio")
    lab_core_count = sum(1 for entry in entries if entry["source_project"] == "labutopia")

    lines = [
        "# 实验室条目总览",
        "",
        "这个目录不再只围绕单个对象组织，而是统一收拢 `AutoBio` 与 `LabUtopia` 中适合 benchmark 复用的实验室条目，包括独立对象、组合对象、场景内对象引用、完整场景，以及少量仍然有参考价值的场景相关文件。",
        "",
        "当前公开维护的核心产物有四类；另外，本地生成时还会额外产出 protocol 匹配结果文件，默认不纳入版本控制。",
        "",
        "- `README.md`：总览、分类规则、可视化清单",
        "- `benchmark_core_inventory.json`：机器可读的核心条目清单",
        "- `preview_manifest.json`：预览图索引",
        "- `previews/`：脚本生成的预览图",
        "- `protocol_min_v1_with_inventory.jsonl` / `protocol_min_v1_inventory_matches.jsonl` / `protocol_min_v1_inventory_matches.stats.json`：本地生成的 protocol 匹配结果",
        "",
        "## 1. 总览",
        "",
        make_table(["来源仓库", "组织方式", "当前可见层级", "核心条目数", "主要路径"], repo_rows),
        "",
        "```mermaid",
        "flowchart LR",
        "    A[AutoBio] --> A1[独立对象]",
        "    A --> A2[组合对象]",
        "    A --> A3[完整场景]",
        "    B[LabUtopia] --> B1[场景内对象引用]",
        "    B --> B2[完整场景]",
        "    B --> B3[场景相关文件]",
        "    A1 --> C[合并后的实验室条目总表]",
        "    A2 --> C",
        "    A3 --> C",
        "    B1 --> C",
        "    B2 --> C",
        "    B3 --> C",
        "    C --> D[核心条目 29 项]",
        "```",
        "",
        f"当前核心条目共 {len(entries)} 项，其中 `AutoBio` {auto_core_count} 项，`LabUtopia` {lab_core_count} 项。",
        "",
        "## 2. 统一口径",
        "",
        "这里统一使用“实验室条目”作为总称，不再把所有东西都叫作 asset。判断规则如下：",
        "",
        make_table(["标识", "中文解释", "是否独立文件", "典型路径"], type_rows),
        "",
        "补充说明：`LabUtopia` 的很多对象当前仍然是“场景里的对象引用”，所以预览图使用的是场景缩略图叠加对象标签，而不是把对象单独拆出来后的独立渲染。",
        "",
        "## 3. 上游结构",
        "",
        "- `AutoBio` 的主脉络是 `autobio/assets/` + `autobio/model/`。前者更偏原始对象与部件，后者更偏装配入口、仪器入口、机器人入口与完整场景入口。",
        "- `LabUtopia` 的主脉络是 `assets/chemistry_lab/`。它本质上更偏 scene-first，很多对象只能通过 `xxx.usd#/World/...` 这种场景内路径来引用。",
        "- 因此两者合并时，不能只看独立对象；必须把场景、场景内对象引用和组合对象一起纳入统一清单。",
        "",
        "## 4. 全部资产 / 场景",
        "",
        "这一章展示的是上游范围内所有值得盘点和可视化的条目，不等于最终全部纳入 benchmark。少数上游条目如果存在缺失 mesh 或坏引用，会使用结构卡片代替失败 placeholder。",
        "",
        "### 4.1 场景内对象引用",
        "",
        make_table(["预览", "来源", "名称", "代表路径", "所在场景"], scene_object_rows),
        "",
        "### 4.2 独立对象",
        "",
        make_table(["预览", "来源", "名称", "路径"], standalone_rows),
        "",
        "### 4.3 组合对象",
        "",
        make_table(["预览", "来源", "类别", "名称", "路径"], composite_rows),
        "",
        "### 4.4 完整场景与场景相关文件",
        "",
        make_table(["预览", "来源", "类别", "名称", "路径", "说明"], scene_rows),
        "",
        "## 5. 筛选后的 Benchmark 资产 / 场景",
        "",
        "这一节对应 `benchmark_core_inventory.json`。它只保留当前 benchmark 直接需要复用的核心条目，而不是上游仓库的全部文件。",
        "",
        "### 5.1 纳入标准",
        "",
        "只有同时满足下面这些条件的条目，才会进入这一章：",
        "",
        "1. 能直接服务 benchmark 任务，而不是只提供环境背景。",
        "2. 能稳定归入一个明确的语义类别，并绑定 `match_group` 与别名集合。",
        "3. 能整理成结构化数据单元，而不只是上游仓库里的孤立文件。",
        "4. 粒度适合题目构造与 protocol 匹配，不会过细到单个环境碎片，也不会过粗到整张场景。",
        "5. 至少具备可追溯的来源路径、用途说明和可视化状态，便于后续扩展与人工核查。",
        "",
        "### 5.2 核心条目表",
        "",
        make_table(
            ["预览", "条目名称", "来源", "层级", "匹配组", "别名", "用途", "本地相对路径", "可视化状态", "原始链接"],
            core_rows,
        ),
        "",
        "## 6. 当前结论",
        "",
        "- 现在的目录口径已经从“只看 asset”改成“统一看实验室条目”。",
        "- `AutoBio` 更适合提供独立对象、组合对象和可执行的完整场景。",
        "- `LabUtopia` 更适合提供场景内对象引用、化学实验室场景和场景上下文。",
        "- 后续如果要继续扩 benchmark，优先在这份核心条目表上补别名、补用途、补协议匹配结果，而不是再分叉新的清单文件。",
        "",
    ]
    README_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if PREVIEW_ROOT.exists():
        shutil.rmtree(PREVIEW_ROOT)
    ensure_dir(PREVIEW_ROOT)
    manifest = build_preview_manifest()
    write_readme(manifest)
    print(json.dumps({"preview_manifest": rel_from_bench(MANIFEST_PATH)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
