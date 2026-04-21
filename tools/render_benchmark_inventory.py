#!/usr/bin/env python
from __future__ import annotations

import html
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
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

try:
    from pxr import Gf, Usd, UsdGeom
except Exception:
    Gf = None
    Usd = None
    UsdGeom = None


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
AUTOBIO_BLOB_ROOT = "https://github.com/autobio-bench/AutoBio/blob/main"
LABUTOPIA_BLOB_ROOT = f"https://github.com/{LABUTOPIA_REPO}/blob/main"
_AUTOBIO_PLUGIN_LOADED = False

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
SCENE_WIDTH = 360
SCENE_HEIGHT = 240


@dataclass
class ResolvedMesh:
    mesh: trimesh.Trimesh
    source_name: str
    fallback_color: tuple[int, int, int] | None = None


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


def readme_target(path: str) -> tuple[str, str | None]:
    fragment: str | None = None
    if "#" in path:
        path, fragment = path.split("#", 1)
    clean = path.removeprefix("data/benchmark_inventory/")
    if clean.startswith("autobio/"):
        return f"files/autobio/{clean}", fragment
    if clean.startswith("assets/"):
        return f"files/labutopia/{clean}", fragment
    return clean, fragment


def short_path_label(path: str) -> str:
    clean = path.split("#", 1)[0].rstrip("/")
    name = Path(clean).name or clean
    if not Path(clean).suffix and not name.endswith("/"):
        return f"{name}/"
    return name


def readme_href(path: str) -> tuple[str, str | None] | None:
    if path.startswith("/"):
        return None
    target, fragment = readme_target(path)
    if (BENCH_ROOT / target).exists():
        return target, fragment
    if path.startswith("autobio/"):
        return f"{AUTOBIO_BLOB_ROOT}/{path}", fragment
    if path.startswith("assets/"):
        return f"{LABUTOPIA_BLOB_ROOT}/{path}", fragment
    return target, fragment


def path_link(path: str, label: str | None = None) -> str:
    href = readme_href(path)
    if href is None:
        return f"<code>{path}</code>"
    target, fragment = href
    text = f"[{label or short_path_label(path)}]({target})"
    if fragment:
        return f"{text}<br><code>#{fragment}</code>"
    return text


def path_cell(paths: list[str] | str) -> str:
    if isinstance(paths, str):
        return path_link(paths)
    return "<br>".join(path_link(item) for item in paths)


def image_cell(path: str | None, alt: str, width: int = 200) -> str:
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
    note = detail or "Metadata fallback"
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
        return "Missing mesh in upstream source"
    if "mesh" in message and "not found" in message:
        return "Broken XML or mesh reference"
    if "plugin" in message:
        return "Missing upstream plugin dependency"
    return "Fallback metadata preview"


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

AUTOBIO_MJCF_MESH_RENDER_SOURCES = {
    "model/object/pipette.gen.xml": AUTOBIO_ROOT / "assets" / "tool" / "pipette",
}

AUTOBIO_PROXY_PREVIEWS = {
    "model/robot/dualrm.xml": "dualrm",
    "model/robot/piper.xml": "piper",
    "model/hand/shadowhand_left.xml": "shadowhand_left",
    "model/hand/shadowhand_right.xml": "shadowhand_right",
    "model/hand/shadowhand_right_mjx.xml": "shadowhand_right",
}


def fallback_render_source(source_path: Path) -> tuple[Path, str, str] | None:
    resolved = resolve_autobio_render_source(source_path)
    try:
        relative = resolved.relative_to(AUTOBIO_ROOT).as_posix()
    except ValueError:
        return None
    return AUTOBIO_PREVIEW_FALLBACKS.get(relative)


def fallback_proxy_kind(source_path: Path) -> str | None:
    resolved = resolve_autobio_render_source(source_path)
    try:
        relative = resolved.relative_to(AUTOBIO_ROOT).as_posix()
    except ValueError:
        return None
    return AUTOBIO_PROXY_PREVIEWS.get(relative)


def preferred_mesh_render_source(source_path: Path) -> Path | None:
    resolved = resolve_autobio_render_source(source_path)
    try:
        relative = resolved.relative_to(AUTOBIO_ROOT).as_posix()
    except ValueError:
        return None
    return AUTOBIO_MJCF_MESH_RENDER_SOURCES.get(relative)


def vertical_gradient(
    size: tuple[int, int],
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> Image.Image:
    width, height = size
    top_arr = np.array(top, dtype=np.float32)
    bottom_arr = np.array(bottom, dtype=np.float32)
    ramp = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    colors = top_arr * (1.0 - ramp) + bottom_arr * ramp
    image = np.repeat(colors[:, None, :], width, axis=1).astype(np.uint8)
    return Image.fromarray(image, mode="RGB")


def make_proxy_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    scale = 2
    image = vertical_gradient(
        (SCENE_WIDTH * scale, SCENE_HEIGHT * scale),
        (249, 251, 253),
        (227, 233, 240),
    ).convert("RGBA")
    return image, ImageDraw.Draw(image)


def add_ground_shadow(image: Image.Image, bbox: tuple[int, int, int, int], opacity: int = 82) -> None:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse(bbox, fill=(44, 62, 80, opacity))
    blurred = layer.filter(ImageFilter.GaussianBlur(radius=18))
    image.alpha_composite(blurred)


def draw_segment(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    width: int,
    base: tuple[int, int, int],
    highlight: tuple[int, int, int] | None = None,
) -> None:
    draw.line((start, end), fill=base, width=width)
    radius = width // 2
    for cx, cy in (start, end):
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=base)
    if highlight:
        inner = max(4, width // 3)
        draw.line((start, end), fill=highlight, width=inner)


def draw_joint(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    radius: int,
    outer: tuple[int, int, int],
    inner: tuple[int, int, int],
) -> None:
    cx, cy = center
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=outer)
    inner_radius = max(3, radius - 8)
    draw.ellipse(
        (cx - inner_radius, cy - inner_radius, cx + inner_radius, cy + inner_radius),
        fill=inner,
    )


def finalize_proxy_image(image: Image.Image, title: str) -> Image.Image:
    proxy = image.resize((SCENE_WIDTH, SCENE_HEIGHT), Image.LANCZOS).convert("RGB")
    proxy = ImageOps.autocontrast(proxy, cutoff=1)
    return add_label(proxy, title)


def render_dualarm_proxy(title: str) -> Image.Image:
    image, draw = make_proxy_canvas()
    add_ground_shadow(image, (110, 338, 610, 440))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((176, 250, 544, 360), radius=34, fill=(69, 82, 96))
    draw.rounded_rectangle((200, 226, 520, 286), radius=28, fill=(91, 106, 122))
    draw.rounded_rectangle((304, 124, 416, 252), radius=24, fill=(231, 236, 242))
    draw.rounded_rectangle((286, 102, 434, 150), radius=24, fill=(245, 248, 250))
    draw.rounded_rectangle((350, 66, 370, 126), radius=10, fill=(90, 102, 118))
    draw.rounded_rectangle((324, 50, 396, 82), radius=12, fill=(46, 58, 72))
    draw.rounded_rectangle((334, 58, 386, 74), radius=8, fill=(121, 208, 255))
    for wheel_x in (216, 504):
        draw.ellipse((wheel_x - 38, 336, wheel_x + 38, 410), fill=(28, 37, 48))
        draw.ellipse((wheel_x - 24, 350, wheel_x + 24, 396), fill=(109, 123, 140))

    left_points = [(300, 164), (238, 152), (192, 184), (166, 224)]
    right_points = [(420, 164), (482, 152), (528, 184), (554, 224)]
    for points in (left_points, right_points):
        draw_segment(draw, points[0], points[1], 28, (233, 238, 243), (252, 252, 252))
        draw_segment(draw, points[1], points[2], 26, (241, 244, 247), (255, 255, 255))
        draw_segment(draw, points[2], points[3], 22, (232, 237, 242), (255, 255, 255))
        for joint in points[1:-1]:
            draw_joint(draw, joint, 16, (88, 98, 112), (198, 207, 218))
    for claw_x, claw_y, direction in ((166, 224, -1), (554, 224, 1)):
        draw.line((claw_x, claw_y, claw_x + 20 * direction, claw_y - 16), fill=(47, 55, 66), width=8)
        draw.line((claw_x, claw_y, claw_x + 20 * direction, claw_y + 16), fill=(47, 55, 66), width=8)

    return finalize_proxy_image(image, title)


def render_piper_proxy(title: str) -> Image.Image:
    image, draw = make_proxy_canvas()
    add_ground_shadow(image, (154, 344, 586, 430))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((244, 270, 440, 354), radius=28, fill=(56, 64, 75))
    draw.rounded_rectangle((284, 208, 398, 286), radius=26, fill=(230, 233, 237))
    draw.rounded_rectangle((312, 170, 370, 230), radius=20, fill=(246, 247, 248))
    arm_points = [(340, 184), (336, 132), (388, 96), (462, 112), (516, 152)]
    arm_colors = [
        ((231, 235, 240), (255, 255, 255)),
        ((221, 44, 44), (247, 118, 118)),
        ((236, 239, 243), (255, 255, 255)),
        ((221, 44, 44), (247, 118, 118)),
    ]
    widths = [30, 28, 24, 20]
    for idx, (start, end) in enumerate(zip(arm_points, arm_points[1:])):
        base, highlight = arm_colors[idx]
        draw_segment(draw, start, end, widths[idx], base, highlight)
        draw_joint(draw, end, max(12, widths[idx] // 2 + 2), (63, 72, 84), (188, 195, 204))
    draw.line((516, 152, 548, 144), fill=(40, 49, 60), width=8)
    draw.line((516, 152, 544, 172), fill=(40, 49, 60), width=8)
    draw.ellipse((320, 274, 364, 318), fill=(190, 198, 208))
    return finalize_proxy_image(image, title)


def render_shadowhand_proxy(title: str, mirrored: bool = False) -> Image.Image:
    image, draw = make_proxy_canvas()
    add_ground_shadow(image, (116, 338, 618, 424))
    draw = ImageDraw.Draw(image)
    draw_segment(draw, (182, 288), (278, 248), 52, (70, 77, 87), (110, 118, 128))
    palm = [(266, 154), (360, 136), (428, 194), (384, 284), (286, 284), (242, 212)]
    draw.polygon(palm, fill=(54, 61, 71))
    highlight = [(280, 168), (352, 154), (404, 198), (374, 256), (300, 254), (264, 202)]
    draw.polygon(highlight, fill=(95, 103, 114))

    finger_bases = [(294, 166), (324, 152), (354, 146), (384, 152)]
    finger_targets = [(270, 84), (326, 70), (378, 76), (430, 98)]
    for base, target in zip(finger_bases, finger_targets):
        mid = ((base[0] + target[0]) // 2, (base[1] + target[1]) // 2 - 10)
        tip = (target[0] + 10, target[1] + 34)
        draw_segment(draw, base, mid, 20, (44, 50, 59), (88, 95, 106))
        draw_joint(draw, mid, 10, (36, 42, 51), (151, 160, 170))
        draw_segment(draw, mid, tip, 18, (55, 61, 71), (100, 107, 118))
    thumb = [(262, 208), (218, 184), (180, 160), (158, 124)]
    for start, end, width in zip(thumb, thumb[1:], (22, 18, 16)):
        draw_segment(draw, start, end, width, (43, 49, 58), (94, 100, 110))

    if mirrored:
        image = ImageOps.mirror(image)
    return finalize_proxy_image(image, title)


def render_proxy_preview(kind: str, title: str) -> Image.Image:
    if kind == "dualrm":
        return render_dualarm_proxy(title)
    if kind == "piper":
        return render_piper_proxy(title)
    if kind == "shadowhand_left":
        return render_shadowhand_proxy(title, mirrored=False)
    if kind == "shadowhand_right":
        return render_shadowhand_proxy(title, mirrored=True)
    return reference_card(title, "metadata card", "Proxy preview unavailable")


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


def composite_on_light_background(
    image: Image.Image,
    diff_threshold: int = 16,
    dark_background_threshold: int = 40,
) -> Image.Image:
    rgb = image.convert("RGB")
    arr = np.asarray(rgb)
    bg = corner_background_color(rgb)
    if float(bg.mean()) > dark_background_threshold:
        return rgb
    diff = np.abs(arr.astype(np.int16) - bg.astype(np.int16)).max(axis=2)
    mask = diff > diff_threshold
    if mask.mean() < 0.002:
        return rgb
    alpha = Image.fromarray((mask.astype(np.uint8) * 255), mode="L").filter(ImageFilter.GaussianBlur(radius=1.4))
    background = vertical_gradient(
        (rgb.width, rgb.height),
        (250, 251, 253),
        (232, 238, 244),
    ).convert("RGBA")
    shadow_alpha = ImageEnhance.Brightness(alpha.filter(ImageFilter.GaussianBlur(radius=10))).enhance(0.42)
    shadow = Image.new("RGBA", rgb.size, (52, 64, 79, 0))
    shadow.putalpha(shadow_alpha)
    shadow = ImageChops.offset(shadow, 7, 9)
    composed = Image.alpha_composite(background, shadow)
    foreground = rgb.convert("RGBA")
    foreground.putalpha(alpha)
    composed = Image.alpha_composite(composed, foreground)
    return composed.convert("RGB")


def enhance_preview_image(image: Image.Image, brighten: float = 1.04, contrast: float = 1.08) -> Image.Image:
    enhanced = ImageOps.autocontrast(image.convert("RGB"), cutoff=1)
    enhanced = ImageEnhance.Brightness(enhanced).enhance(brighten)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast)
    return enhanced


def soft_enhance_preview_image(image: Image.Image, brighten: float = 1.05, contrast: float = 1.04) -> Image.Image:
    enhanced = ImageEnhance.Brightness(image.convert("RGB")).enhance(brighten)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast)
    return enhanced


def inferred_preview_color(source_name: str, title: str) -> tuple[int, int, int]:
    text = f"{source_name} {title}".lower()
    if any(token in text for token in ["knob", "button", "connector", "handle", "cap", "lid"]):
        return (92, 151, 224)
    if "tip" in text:
        return (120, 168, 232)
    if any(token in text for token in ["cell dish", "petri", "beaker", "conical", "glass", "cylinder"]):
        return (232, 242, 249)
    if any(token in text for token in ["tube", "vial", "cryovial"]):
        return (226, 238, 247)
    if "pipette" in text:
        return (240, 242, 246)
    if "plate" in text:
        return (228, 233, 239)
    if any(token in text for token in ["rack", "box", "platform", "plat"]):
        return (103, 148, 214)
    if any(token in text for token in ["centrifuge", "thermal", "mixer", "vortex", "furnace", "drying", "heat device"]):
        return (233, 237, 242)
    if any(token in text for token in ["cabinet", "table"]):
        return (210, 214, 220)
    return (121, 146, 191)


def mesh_face_colors(mesh: trimesh.Trimesh, source_name: str, title: str, fallback_color: tuple[int, int, int] | None = None) -> np.ndarray:
    force_inferred = not source_name.startswith("/World/") and any(
        token in title.lower()
        for token in [
            "pipette",
            "plate",
            "tube",
            "dish",
            "tip",
            "rack",
            "box",
            "cryovial",
        ]
    )
    if force_inferred:
        color = np.array(fallback_color or inferred_preview_color(source_name, title), dtype=np.uint8)
        rgba = np.concatenate([color, np.array([255], dtype=np.uint8)])
        return np.tile(rgba, (len(mesh.faces), 1))

    try:
        visual = mesh.visual.to_color()
        face_colors = np.asarray(visual.face_colors)
    except Exception:
        face_colors = np.empty((0, 4), dtype=np.uint8)
    if len(face_colors) == len(mesh.faces):
        rgb = face_colors[:, :3].astype(np.float32)
        spread = float(np.ptp(rgb, axis=0).max()) if len(rgb) else 0.0
        mean = rgb.mean(axis=0) if len(rgb) else np.zeros(3, dtype=np.float32)
        if not (spread < 2.5 and np.allclose(mean, np.array([102.0, 102.0, 102.0]), atol=4.0)):
            return face_colors
    color = np.array(fallback_color or inferred_preview_color(source_name, title), dtype=np.uint8)
    rgba = np.concatenate([color, np.array([255], dtype=np.uint8)])
    return np.tile(rgba, (len(mesh.faces), 1))


def shaded_face_colors(vertices: np.ndarray, faces: np.ndarray, face_colors: np.ndarray) -> np.ndarray:
    tri_vertices = vertices[faces]
    normals = np.cross(tri_vertices[:, 1] - tri_vertices[:, 0], tri_vertices[:, 2] - tri_vertices[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = normals / np.maximum(lengths, 1e-8)
    key_light = np.array([0.65, -0.45, 0.72], dtype=np.float32)
    fill_light = np.array([-0.25, 0.30, 0.58], dtype=np.float32)
    key_light /= np.linalg.norm(key_light)
    fill_light /= np.linalg.norm(fill_light)
    key = np.clip(normals @ key_light, 0.0, 1.0)
    fill = np.clip(normals @ fill_light, 0.0, 1.0)
    intensity = 0.78 + 0.15 * key + 0.07 * fill
    rim = np.clip(1.0 - np.abs(normals[:, 2]), 0.0, 1.0) * 0.10
    base = face_colors[:, :3].astype(np.float32) / 255.0
    shaded = np.clip(base * intensity[:, None] + rim[:, None], 0.0, 1.0)
    alpha = face_colors[:, 3:4].astype(np.float32) / 255.0
    return np.concatenate([shaded, alpha], axis=1)


def render_resolved_meshes(meshes: list[ResolvedMesh], out_path: Path, title: str) -> None:
    if not meshes:
        save_image(reference_card(title, "metadata card", "No renderable mesh found"), out_path)
        return

    vertex_blocks: list[np.ndarray] = []
    face_blocks: list[np.ndarray] = []
    color_blocks: list[np.ndarray] = []
    vertex_offset = 0
    for entry in meshes:
        mesh = entry.mesh.copy()
        if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            continue
        vertex_blocks.append(mesh.vertices.copy())
        face_blocks.append(mesh.faces.copy() + vertex_offset)
        color_blocks.append(mesh_face_colors(mesh, entry.source_name, title, entry.fallback_color))
        vertex_offset += len(mesh.vertices)

    if not vertex_blocks:
        save_image(reference_card(title, "metadata card", "No renderable mesh found"), out_path)
        return

    vertices = np.concatenate(vertex_blocks, axis=0)
    faces = np.concatenate(face_blocks, axis=0)
    face_colors = np.concatenate(color_blocks, axis=0)
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
        facecolors=shaded_face_colors(vertices, faces, face_colors),
        edgecolor=(0.13, 0.18, 0.25, 0.08),
        linewidth=0.10,
    )
    ax.add_collection3d(collection)
    span = 0.64
    ax.set_xlim(-span, span)
    ax.set_ylim(-span, span)
    ax.set_zlim(-span, span)
    ax.view_init(elev=23, azim=42)
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
    raw = soft_enhance_preview_image(raw, brighten=1.08, contrast=1.05)
    tmp_path.unlink(missing_ok=True)
    save_image(add_label(raw, title), out_path)


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
    pil_image = Image.fromarray(image).convert("RGB")
    pil_image = composite_on_light_background(pil_image)
    pil_image = crop_to_content(pil_image, (SCENE_WIDTH, SCENE_HEIGHT))
    pil_image = soft_enhance_preview_image(pil_image, brighten=1.06, contrast=1.04)
    save_image(add_label(pil_image, title), out_path)


def load_mesh_entries(source: Path) -> list[ResolvedMesh]:
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
            and "pusher" not in path.stem.lower()
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
    meshes: list[ResolvedMesh] = []
    for candidate in candidates:
        try:
            loaded = trimesh.load(candidate, force="mesh", process=False)
        except Exception:
            continue
        if isinstance(loaded, trimesh.Trimesh) and len(loaded.vertices) and len(loaded.faces):
            meshes.append(ResolvedMesh(loaded, candidate.name))
    return meshes


def render_mesh_preview(source: Path, out_path: Path, title: str) -> None:
    render_resolved_meshes(load_mesh_entries(source), out_path, title)


def write_preview(source_path: Path, out_path: Path, title: str, preview_kind: str) -> None:
    try:
        if preview_kind == "mjcf":
            mesh_override = preferred_mesh_render_source(source_path)
            if mesh_override is not None:
                render_mesh_preview(mesh_override, out_path, title)
                return
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
                save_image(reference_card(title, "metadata card", fallback_reason), out_path)
                return
        proxy_kind = fallback_proxy_kind(source_path)
        if proxy_kind is not None:
            save_image(render_proxy_preview(proxy_kind, title), out_path)
            return
        save_image(reference_card(title, "metadata card", humanize_render_error(exc)), out_path)


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


def enhance_labutopia_thumbnail(image: Image.Image) -> Image.Image:
    enhanced = enhance_preview_image(image, brighten=1.10, contrast=1.06)
    bg = corner_background_color(enhanced)
    if float(bg.mean()) < 55:
        enhanced = composite_on_light_background(enhanced, diff_threshold=12, dark_background_threshold=55)
        enhanced = enhance_preview_image(enhanced, brighten=1.08, contrast=1.10)
    return enhanced


def triangulate_face_indices(face_counts: list[int], face_indices: list[int]) -> np.ndarray:
    triangles: list[list[int]] = []
    offset = 0
    for count in face_counts:
        polygon = face_indices[offset : offset + count]
        if count >= 3:
            for idx in range(1, count - 1):
                triangles.append([polygon[0], polygon[idx], polygon[idx + 1]])
        offset += count
    if not triangles:
        return np.empty((0, 3), dtype=np.int32)
    return np.asarray(triangles, dtype=np.int32)


def usd_display_color(prim: Any) -> tuple[int, int, int] | None:
    if UsdGeom is None:
        return None
    primvar = UsdGeom.Gprim(prim).GetDisplayColorPrimvar()
    if not primvar or not primvar.HasValue():
        return None
    try:
        value = primvar.Get()
    except Exception:
        return None
    if not value:
        return None
    colors = np.asarray([[float(color[0]), float(color[1]), float(color[2])] for color in value], dtype=np.float32)
    mean = np.clip(colors.mean(axis=0), 0.0, 1.0)
    if float(mean.mean()) < 0.45:
        return None
    return tuple(int(round(channel * 255)) for channel in mean)


def load_labutopia_prim_meshes(stage_path: Path, prim_path: str, title: str) -> list[ResolvedMesh]:
    if Usd is None or UsdGeom is None or Gf is None:
        return []
    stage = Usd.Stage.Open(str(stage_path))
    if stage is None:
        return []
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        return []

    xform_cache = UsdGeom.XformCache()
    meshes: list[ResolvedMesh] = []
    for child in Usd.PrimRange(prim):
        if child.GetTypeName() != "Mesh":
            continue
        mesh = UsdGeom.Mesh(child)
        try:
            points = mesh.GetPointsAttr().Get() or []
            face_counts = mesh.GetFaceVertexCountsAttr().Get() or []
            face_indices = mesh.GetFaceVertexIndicesAttr().Get() or []
        except Exception:
            continue
        if not points or not face_counts or not face_indices:
            continue
        faces = triangulate_face_indices(list(face_counts), list(face_indices))
        if len(faces) == 0:
            continue
        transform = xform_cache.GetLocalToWorldTransform(child)
        world_points = np.asarray(
            [transform.Transform(Gf.Vec3d(float(point[0]), float(point[1]), float(point[2]))) for point in points],
            dtype=np.float64,
        )
        fallback_color = usd_display_color(child) or inferred_preview_color(str(child.GetPath()), title)
        mesh_obj = trimesh.Trimesh(vertices=world_points, faces=faces, process=False)
        meshes.append(ResolvedMesh(mesh_obj, str(child.GetPath()), fallback_color))
    return meshes


def save_labutopia_object_preview(
    scene_path: str,
    object_paths: list[str],
    out_path: Path,
    title: str,
) -> None:
    scene_file = LABUTOPIA_LOCAL_ROOT / scene_path
    for object_path in object_paths:
        meshes = load_labutopia_prim_meshes(scene_file, object_path, title)
        if meshes:
            render_resolved_meshes(meshes, out_path, title)
            return
    subtitle = object_paths[0] if len(object_paths) == 1 else f"{object_paths[0]} ..."
    save_labutopia_scene_preview(scene_path, out_path, title, subtitle)


def save_labutopia_reference_preview(local_relative_path: str, out_path: Path, title: str) -> None:
    scene_local_path, prim_path = local_relative_path.split("#", 1)
    scene_file = REPO_ROOT / scene_local_path
    prim_path = prim_path if prim_path.startswith("/") else f"/{prim_path.lstrip('/')}"
    meshes = load_labutopia_prim_meshes(scene_file, prim_path, title)
    if meshes:
        render_resolved_meshes(meshes, out_path, title)
        return
    scene_path = relative_path_from_labutopia_local(scene_local_path)
    save_labutopia_scene_preview(scene_path, out_path, title, prim_path)


def save_labutopia_scene_preview(scene_path: str, out_path: Path, title: str, subtitle: str | None = None) -> None:
    image = load_labutopia_thumb(scene_path).resize((SCENE_WIDTH, SCENE_HEIGHT), Image.LANCZOS)
    image = enhance_labutopia_thumbnail(image)
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
    ("muffle furnace", ["/World/MuffleFurnace"], "assets/chemistry_lab/lab_001/lab_001.usd"),
    ("rack / platform", ["/World/target_plat"], "assets/chemistry_lab/hard_task/Scene1_hard.usd"),
    ("table surface", ["/World/table/surface", "/World/table/surface/mesh"], "assets/chemistry_lab/lab_003/lab_003.usd"),
]


REFERENCE_KIND_LABELS = {
    "standalone_mesh_root": "独立对象",
    "package_entrypoint": "组合对象",
    "scene_prim_reference": "场景内对象引用",
    "scene": "完整场景",
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
    "ready_mjcf_scene": "可直接按 MJCF 场景渲染",
    "downloaded_usd_requires_conversion": "当前使用 USD 场景缩略图展示",
    "downloaded_usd_scene": "当前使用 USD 场景缩略图展示",
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
        save_labutopia_object_preview(scene_path, object_paths, out_path, family)
        manifest["labutopia_scene_objects"][family] = rel_from_bench(out_path)

    for entry in load_core_entries():
        out_path = PREVIEW_ROOT / "core" / entry["source_project"] / f"{slugify(entry['entry_id'])}.png"
        if entry["source_project"] == "labutopia" and entry["reference_kind"] == "scene_prim_reference":
            save_labutopia_reference_preview(entry["local_relative_path"], out_path, entry["entry_name"])
        elif entry["source_project"] == "labutopia":
            scene_path = relative_path_from_labutopia_local(entry["local_relative_path"]).split("#", 1)[0]
            label = entry["local_relative_path"].split("#", 1)[1] if "#" in entry["local_relative_path"] else None
            save_labutopia_scene_preview(scene_path, out_path, entry["entry_name"], label)
        else:
            source = resolve_autobio_render_source(REPO_ROOT / entry["local_relative_path"])
            kind = "mjcf" if entry["reference_kind"] in {"package_entrypoint", "scene"} else "mesh"
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
                f"{path_link('autobio/assets', 'assets/')}<br>{path_link('autobio/model', 'model/')}",
            ]
        ),
        TableRow(
            [
                "LabUtopia",
                "场景优先，核心文件是 USD 场景",
                f"场景内对象引用 {len(LAB_SCENE_OBJECTS)}<br>完整场景 {len(LAB_SCENES)}<br>场景相关文件 {len(extra_lab_scene_files())}",
                str(core_counts["labutopia"]),
                path_link("assets/chemistry_lab", "chemistry_lab/"),
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
                f"{path_link('autobio/model/scene/lab.xml')}<br>{path_link('assets/chemistry_lab/lab_001/lab_001.usd')}",
            ]
        ),
        TableRow(
            [
                "`standalone_mesh_root`",
                "独立对象的 mesh 根入口，通常对应单个对象或单个对象目录。",
                "是",
                path_link("autobio/assets/container/pcr_plate_96well_vis.obj"),
            ]
        ),
        TableRow(
            [
                "`package_entrypoint`",
                "组合对象入口，会继续引用多个部件、材质或子文件。",
                "是",
                path_link("autobio/model/instrument/centrifuge_eppendorf_5430.xml"),
            ]
        ),
        TableRow(
            [
                "`scene_prim_reference`",
                "场景内对象引用，依附在某个 USD 场景里，本身不是独立文件。",
                "否",
                path_link("assets/chemistry_lab/lab_001/lab_001.usd#/World/conical_bottle02"),
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
                    path_link(scene_path),
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


def html_anchor(href: str, label: str) -> str:
    return f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'


def path_link_html(path: str, label: str | None = None) -> str:
    href = readme_href(path)
    if href is None:
        return f"<code>{html.escape(path)}</code>"
    target, fragment = href
    text = html_anchor(target, label or short_path_label(path))
    if fragment:
        return f"{text}<br><code>#{html.escape(fragment)}</code>"
    return text


def core_inventory_html_blocks(
    manifest: dict[str, dict[str, str]],
    entries: list[dict[str, Any]],
) -> str:
    blocks: list[str] = []
    for index, entry in enumerate(entries):
        number = f"{index:03d}"
        image_path = manifest["core_entries"].get(entry["entry_id"])
        image_html = (
            f'<img src="{html.escape(image_path, quote=True)}" width="420" alt="{html.escape(entry["entry_name"], quote=True)}">'
            if image_path
            else ""
        )
        aliases = "<br>".join(html.escape(alias) for alias in entry["aliases"])
        original_link = html_anchor(entry["original_url"], "源文件")
        block = "\n".join(
            [
                '<table>',
                "  <tr>",
                '    <td valign="top" width="450">',
                f"      {image_html}",
                "    </td>",
                '    <td valign="top">',
                f'      <p><strong><code>{number}</code> {html.escape(entry["entry_name"])}</strong></p>',
                f'      <p><strong>来源：</strong>{html.escape(source_label(entry["source_project"]))}<br>',
                f'      <strong>层级：</strong>{html.escape(REFERENCE_KIND_LABELS[entry["reference_kind"]])}<br>',
                f'      <strong>匹配组：</strong><code>{html.escape(entry["match_group"])}</code></p>',
                f'      <p><strong>用途：</strong>{html.escape(entry["purpose"])}</p>',
                f'      <p><strong>本地文件：</strong>{path_link_html(entry["local_relative_path"])}</p>',
                f'      <p><strong>可视化状态：</strong>{html.escape(render_status_label(entry["render_status"]))}<br>',
                f'      <strong>原始链接：</strong>{original_link}</p>',
                "      <details>",
                "        <summary><strong>别名</strong></summary>",
                f"        <p>{aliases}</p>",
                "      </details>",
                "    </td>",
                "  </tr>",
                "</table>",
            ]
        )
        blocks.append(block)
    return "\n\n".join(blocks)


def write_readme(manifest: dict[str, dict[str, str]]) -> None:
    entries = load_core_entries()
    repo_rows = repo_overview_rows(entries)
    type_rows = type_overview_rows()
    scene_object_rows = merged_scene_object_rows(manifest)
    standalone_rows = merged_standalone_rows(manifest)
    composite_rows = merged_composite_rows(manifest)
    scene_rows = merged_scene_rows(manifest)
    core_blocks = core_inventory_html_blocks(manifest, entries)

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
        f"    C --> D[核心条目 {len(entries)} 项]",
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
        "这一章展示的是上游范围内所有值得盘点和可视化的条目，不等于最终全部纳入 benchmark。少数上游条目如果缺失 mesh 或存在坏引用，会回退到本地代理预览或信息卡，不再保留失败 placeholder。",
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
        "这一节对应 `benchmark_core_inventory.json`。这里采用最宽的 protocol 口径：凡是能直接服务 protocol 构造、protocol 理解，或者能作为 Level 2 视觉上下文的完整场景，都纳入第 5 章；只把明显属于 Level 3 执行器的 robot / hand / gripper 留在第 4 章。",
        "",
        "### 5.1 纳入标准",
        "",
        "只有同时满足下面这些条件的条目，才会进入这一章：",
        "",
        "1. 条目本身或场景主体必须直接服务 protocol 构造、protocol 理解或 Level 2 的实验上下文表达。",
        "2. 能稳定归入一个明确的语义类别，并绑定 `match_group` 与别名集合。",
        "3. 能整理成结构化数据单元，而不只是上游仓库里的孤立文件。",
        "4. 粒度适合题目构造与 protocol 匹配；完整场景只要提供 protocol 相关仪器、容器、实验台面或实验室上下文，就纳入。",
        "5. 至少具备可追溯的来源路径、用途说明和可视化状态，便于后续扩展与人工核查。",
        "",
        "### 5.2 核心条目表",
        "",
        "这一节改为 HTML 两列布局：左侧固定放大预览图，右侧放条目字段，避免 GitHub Markdown 表格把图片继续压缩。",
        f"当前共 `{len(entries):03d}` 项，编号从 `000` 到 `{len(entries) - 1:03d}`。",
        "",
        core_blocks,
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
