#!/usr/bin/env python
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mujoco
import numpy as np
from PIL import Image

import render_benchmark_inventory as base


MULTIVIEW_ROOT = base.BENCH_ROOT / "multiview"
MULTIVIEW_MANIFEST_PATH = base.BENCH_ROOT / "multiview_manifest.json"
MULTIVIEW_README_PATH = MULTIVIEW_ROOT / "README.md"


@dataclass(frozen=True)
class ViewSpec:
    name: str
    label: str
    mesh_elev: float
    mesh_azim: float
    mjcf_elev: float
    mjcf_azim: float


VIEW_SPECS = [
    ViewSpec("top", "top / upper view", 90, -90, -89, 0),
    ViewSpec("bottom", "bottom / lower view", -90, -90, 89, 0),
    ViewSpec("left", "left side view", 0, 180, -5, -90),
    ViewSpec("right", "right side view", 0, 0, -5, 90),
    ViewSpec("front", "front view", 0, -90, -5, 0),
    ViewSpec("back", "back view", 0, 90, -5, 180),
    ViewSpec("free", "free oblique view", 28, 42, -35, 145),
]


def rel_from_repo(path: Path) -> str:
    return path.relative_to(base.REPO_ROOT).as_posix()


def rel_from_multiview(path: Path) -> str:
    return path.relative_to(MULTIVIEW_ROOT).as_posix()


def filtered_mesh_entries(meshes: list[base.ResolvedMesh]) -> list[base.ResolvedMesh]:
    filtered: list[base.ResolvedMesh] = []
    for entry in meshes:
        mesh = entry.mesh.copy()
        if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            continue
        if not np.isfinite(mesh.vertices).all():
            continue
        filtered.append(base.ResolvedMesh(mesh, entry.source_name, entry.fallback_color))
    return filtered


def merged_mesh_arrays(
    meshes: list[base.ResolvedMesh],
    title: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    vertex_blocks: list[np.ndarray] = []
    face_blocks: list[np.ndarray] = []
    color_blocks: list[np.ndarray] = []
    vertex_offset = 0
    for entry in filtered_mesh_entries(meshes):
        mesh = entry.mesh
        vertex_blocks.append(mesh.vertices.copy())
        face_blocks.append(mesh.faces.copy() + vertex_offset)
        color_blocks.append(base.mesh_face_colors(mesh, entry.source_name, title, entry.fallback_color))
        vertex_offset += len(mesh.vertices)

    if not vertex_blocks:
        raise ValueError("No renderable finite mesh found")

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
    return vertices, faces, face_colors


def render_mesh_view(
    meshes: list[base.ResolvedMesh],
    out_path: Path,
    title: str,
    view: ViewSpec,
) -> None:
    vertices, faces, face_colors = merged_mesh_arrays(meshes, title)
    tri_vertices = vertices[faces]

    dpi = 140
    fig = base.plt.figure(figsize=(base.HIGH_RES_WIDTH / dpi, base.HIGH_RES_HEIGHT / dpi), dpi=dpi)
    ax = fig.add_subplot(111, projection="3d")
    collection = base.Poly3DCollection(
        tri_vertices,
        facecolors=base.shaded_face_colors(vertices, faces, face_colors),
        edgecolor=(0.13, 0.18, 0.25, 0.14),
        linewidth=0.14,
    )
    ax.add_collection3d(collection)
    span = 0.72
    ax.set_xlim(-span, span)
    ax.set_ylim(-span, span)
    ax.set_zlim(-span, span)
    ax.view_init(elev=view.mesh_elev, azim=view.mesh_azim)
    ax.set_box_aspect((1, 1, 1))
    ax.axis("off")
    fig.patch.set_facecolor("#f5f7fa")
    ax.set_facecolor("#f5f7fa")
    fig.subplots_adjust(0, 0, 1, 1)
    ax.set_position([0, 0, 1, 1])
    base.ensure_dir(out_path.parent)
    fig.savefig(out_path, facecolor="#f5f7fa", edgecolor="none")
    base.plt.close(fig)


def render_mesh_views(meshes: list[base.ResolvedMesh], out_dir: Path, title: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for view in VIEW_SPECS:
        out_path = out_dir / f"{view.name}.png"
        render_mesh_view(meshes, out_path, title, view)
        result[view.name] = rel_from_repo(out_path)
    return result


def add_multiview_background_plane(
    scene: mujoco.MjvScene,
    model: mujoco.MjModel,
    extent: float,
    view: ViewSpec,
) -> None:
    if scene.ngeom >= scene.maxgeom:
        return
    center = model.stat.center
    if view.name == "bottom":
        z = float(center[2] + extent * 0.55)
        mat = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, -1.0, 0.0],
                [0.0, 0.0, -1.0],
            ],
            dtype=np.float64,
        )
    else:
        z = float(center[2] - extent * 0.50)
        mat = np.eye(3, dtype=np.float64)

    mujoco.mjv_initGeom(
        scene.geoms[scene.ngeom],
        mujoco.mjtGeom.mjGEOM_PLANE,
        np.array([extent * 8.0, extent * 8.0, 0.1], dtype=np.float64),
        np.array([float(center[0]), float(center[1]), z], dtype=np.float64),
        mat.ravel(),
        np.array([0.93, 0.94, 0.96, 1.0], dtype=np.float32),
    )
    scene.ngeom += 1


def load_mujoco_model(xml_path: Path) -> mujoco.MjModel:
    render_source = base.resolve_autobio_render_source(xml_path)
    if base.is_autobio_render_source(render_source):
        base.load_autobio_plugin()
        with base.temporary_cwd(base.AUTOBIO_ROOT):
            model = mujoco.MjModel.from_xml_path(str(render_source))
    else:
        model = mujoco.MjModel.from_xml_path(str(render_source))
    base.configure_mujoco_preview_model(model)
    return model


def render_mjcf_views(xml_path: Path, out_dir: Path, title: str) -> dict[str, str]:
    render_source = base.resolve_autobio_render_source(xml_path)
    model = load_mujoco_model(xml_path)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    extent = max(float(model.stat.extent), 0.2)
    distance = extent * base.preview_distance_scale(render_source)
    renderer = mujoco.Renderer(model, base.HIGH_RES_HEIGHT, base.HIGH_RES_WIDTH)
    result: dict[str, str] = {}
    try:
        for view in VIEW_SPECS:
            camera = mujoco.MjvCamera()
            camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = model.stat.center
            camera.distance = distance
            camera.azimuth = view.mjcf_azim
            camera.elevation = view.mjcf_elev
            renderer.update_scene(data, camera=camera)
            renderer.scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION] = False
            add_multiview_background_plane(renderer.scene, model, extent, view)
            image = renderer.render()
            out_path = out_dir / f"{view.name}.png"
            base.save_image(Image.fromarray(image).convert("RGB"), out_path)
            result[view.name] = rel_from_repo(out_path)
    finally:
        renderer.close()
    return result


def render_autobio_entry(entry: dict[str, Any], out_dir: Path) -> dict[str, str]:
    source = base.resolve_autobio_render_source(base.REPO_ROOT / entry["local_relative_path"])
    if entry["reference_kind"] in {"package_entrypoint", "scene"}:
        mesh_override = base.preferred_mesh_render_source(source)
        if mesh_override is not None:
            return render_mesh_views(base.load_mesh_entries(mesh_override), out_dir, entry["entry_name"])
        try:
            return render_mjcf_views(source, out_dir, entry["entry_name"])
        except Exception:
            fallback = base.fallback_render_source(source)
            if fallback is None:
                raise
            fallback_source, fallback_kind, _fallback_reason = fallback
            if fallback_kind == "mjcf":
                return render_mjcf_views(fallback_source, out_dir, entry["entry_name"])
            return render_mesh_views(base.load_mesh_entries(fallback_source), out_dir, entry["entry_name"])
    return render_mesh_views(base.load_mesh_entries(source), out_dir, entry["entry_name"])


def labutopia_meshes_for_entry(entry: dict[str, Any]) -> list[base.ResolvedMesh]:
    if entry["reference_kind"] == "scene_prim_reference":
        scene_local_path, prim_path = entry["local_relative_path"].split("#", 1)
        scene_file = base.REPO_ROOT / scene_local_path
        prim_path = prim_path if prim_path.startswith("/") else f"/{prim_path.lstrip('/')}"
        return base.load_labutopia_prim_meshes(scene_file, prim_path, entry["entry_name"])

    scene_path = base.relative_path_from_labutopia_local(entry["local_relative_path"]).split("#", 1)[0]
    meshes = base.load_labutopia_curated_scene_meshes(scene_path, entry["entry_name"])
    if meshes:
        return meshes
    return base.load_labutopia_stage_meshes(base.LABUTOPIA_LOCAL_ROOT / scene_path, entry["entry_name"])


def render_labutopia_entry(entry: dict[str, Any], out_dir: Path) -> dict[str, str]:
    meshes = labutopia_meshes_for_entry(entry)
    return render_mesh_views(meshes, out_dir, entry["entry_name"])


def render_entry(entry: dict[str, Any], out_dir: Path) -> dict[str, str]:
    base.ensure_dir(out_dir)
    if entry["source_project"] == "autobio":
        return render_autobio_entry(entry, out_dir)
    if entry["source_project"] == "labutopia":
        return render_labutopia_entry(entry, out_dir)
    raise ValueError(f"Unsupported source_project: {entry['source_project']}")


def write_manifest(records: list[dict[str, Any]]) -> None:
    manifest = {
        "output_root": rel_from_repo(MULTIVIEW_ROOT),
        "image_size": {"width": base.HIGH_RES_WIDTH, "height": base.HIGH_RES_HEIGHT},
        "view_order": [view.name for view in VIEW_SPECS],
        "views": [
            {
                "name": view.name,
                "label": view.label,
                "mesh_elev": view.mesh_elev,
                "mesh_azim": view.mesh_azim,
                "mjcf_elev": view.mjcf_elev,
                "mjcf_azim": view.mjcf_azim,
            }
            for view in VIEW_SPECS
        ],
        "entries": records,
    }
    MULTIVIEW_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_readme(records: list[dict[str, Any]]) -> None:
    lines = [
        "# 多视角实验室条目图集",
        "",
        "这个目录保存 `benchmark_core_inventory.json` 中 53 个核心实验室条目的 7 视角原生渲染结果。",
        "",
        "## 目录结构",
        "",
        "```text",
        "multiview/",
        "  README.md",
        "  {entry_id}/",
        "    top.png",
        "    bottom.png",
        "    left.png",
        "    right.png",
        "    front.png",
        "    back.png",
        "    free.png",
        "```",
        "",
        "## 生成约束",
        "",
        "- 每个条目固定 7 张图：上、下、左、右、前、后、自由斜视角。",
        "- 图片按条目的 `entry_id` 分文件夹保存。",
        f"- 当前图片尺寸为 `{base.HIGH_RES_WIDTH}x{base.HIGH_RES_HEIGHT}`。",
        "- AutoBio 条目使用 MuJoCo / OBJ / STL 原生渲染。",
        "- LabUtopia 条目使用 USD 几何原生渲染。",
        "- 不做抠图、亮度增强、自动裁剪、文字叠加或手画代理图。",
        "",
        "## 清单",
        "",
        "| 序号 | entry_id | 来源 | 层级 | 图片数 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| `{record['index']:03d}` | `{record['entry_id']}` | "
            f"{record['source_project']} | `{record['reference_kind']}` | {len(record['views'])} |"
        )
    MULTIVIEW_README_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if MULTIVIEW_ROOT.exists():
        shutil.rmtree(MULTIVIEW_ROOT)
    base.ensure_dir(MULTIVIEW_ROOT)

    entries = base.load_core_entries()
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for index, entry in enumerate(entries):
        entry_id = entry["entry_id"]
        out_dir = MULTIVIEW_ROOT / entry_id
        print(f"[{index + 1:02d}/{len(entries):02d}] {entry_id}", flush=True)
        try:
            views = render_entry(entry, out_dir)
        except Exception as exc:
            failures.append({"entry_id": entry_id, "error": str(exc)})
            continue
        records.append(
            {
                "index": index,
                "entry_id": entry_id,
                "entry_name": entry["entry_name"],
                "source_project": entry["source_project"],
                "reference_kind": entry["reference_kind"],
                "local_relative_path": entry["local_relative_path"],
                "views": views,
            }
        )

    if failures:
        raise RuntimeError(json.dumps({"failures": failures}, indent=2, ensure_ascii=False))
    if len(records) != len(entries):
        raise RuntimeError(f"Expected {len(entries)} rendered entries, got {len(records)}")

    write_manifest(records)
    write_readme(records)
    print(
        json.dumps(
            {
                "entries": len(records),
                "views_per_entry": len(VIEW_SPECS),
                "images": len(records) * len(VIEW_SPECS),
                "output_root": rel_from_repo(MULTIVIEW_ROOT),
                "manifest": rel_from_repo(MULTIVIEW_MANIFEST_PATH),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
