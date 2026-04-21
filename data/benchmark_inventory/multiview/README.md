# 多视角实验室条目图集

这个目录保存 `benchmark_core_inventory.json` 中 53 个核心实验室条目的 7 视角原生渲染结果。

## 目录结构

```text
multiview/
  README.md
  {entry_id}/
    top.png
    bottom.png
    left.png
    right.png
    front.png
    back.png
    free.png
```

## 生成约束

- 每个条目固定 7 张图：上、下、左、右、前、后、自由斜视角。
- 图片按条目的 `entry_id` 分文件夹保存。
- 当前图片尺寸为 `840x560`。
- AutoBio 条目使用 MuJoCo / OBJ / STL 原生渲染。
- LabUtopia 条目使用 USD 几何原生渲染。
- 不做抠图、亮度增强、自动裁剪、文字叠加或手画代理图。

## 清单

| 序号 | entry_id | 来源 | 层级 | 图片数 |
| --- | --- | --- | --- | --- |
| `000` | `autobio_cell_dish_100` | autobio | `standalone_mesh_root` | 7 |
| `001` | `autobio_centrifuge_1_5ml_screw` | autobio | `standalone_mesh_root` | 7 |
| `002` | `autobio_centrifuge_10ml` | autobio | `standalone_mesh_root` | 7 |
| `003` | `autobio_centrifuge_1500ul_open` | autobio | `standalone_mesh_root` | 7 |
| `004` | `autobio_centrifuge_15ml_screw` | autobio | `standalone_mesh_root` | 7 |
| `005` | `autobio_centrifuge_50ml` | autobio | `standalone_mesh_root` | 7 |
| `006` | `autobio_centrifuge_50ml_screw` | autobio | `standalone_mesh_root` | 7 |
| `007` | `autobio_cryovial_1_8ml` | autobio | `standalone_mesh_root` | 7 |
| `008` | `autobio_pcr_plate_96well` | autobio | `standalone_mesh_root` | 7 |
| `009` | `autobio_tip_200ul` | autobio | `standalone_mesh_root` | 7 |
| `010` | `autobio_pipette` | autobio | `package_entrypoint` | 7 |
| `011` | `autobio_tip_box_24slot` | autobio | `standalone_mesh_root` | 7 |
| `012` | `autobio_pipette_rack_tri` | autobio | `standalone_mesh_root` | 7 |
| `013` | `autobio_centrifuge_10slot_rack` | autobio | `standalone_mesh_root` | 7 |
| `014` | `autobio_centrifuge_plate_60well` | autobio | `standalone_mesh_root` | 7 |
| `015` | `autobio_centrifuge_5430` | autobio | `package_entrypoint` | 7 |
| `016` | `autobio_centrifuge_5910_ri` | autobio | `package_entrypoint` | 7 |
| `017` | `autobio_centrifuge_tgear_mini` | autobio | `package_entrypoint` | 7 |
| `018` | `autobio_thermal_cycler_c1000` | autobio | `package_entrypoint` | 7 |
| `019` | `autobio_thermal_mixer_eppendorf_c` | autobio | `package_entrypoint` | 7 |
| `020` | `autobio_vortex_mixer_genie_2` | autobio | `package_entrypoint` | 7 |
| `021` | `labutopia_beaker_family` | labutopia | `scene_prim_reference` | 7 |
| `022` | `labutopia_conical_bottle_family` | labutopia | `scene_prim_reference` | 7 |
| `023` | `labutopia_graduated_cylinder_03` | labutopia | `scene_prim_reference` | 7 |
| `024` | `labutopia_glass_rod` | labutopia | `scene_prim_reference` | 7 |
| `025` | `labutopia_test_tube_rack` | labutopia | `scene_prim_reference` | 7 |
| `026` | `labutopia_drying_box_family` | labutopia | `scene_prim_reference` | 7 |
| `027` | `labutopia_heat_device` | labutopia | `scene_prim_reference` | 7 |
| `028` | `labutopia_muffle_furnace` | labutopia | `scene_prim_reference` | 7 |
| `029` | `autobio_scene_bottlecap` | autobio | `scene` | 7 |
| `030` | `autobio_scene_gallery` | autobio | `scene` | 7 |
| `031` | `autobio_scene_gallery2` | autobio | `scene` | 7 |
| `032` | `autobio_scene_insert` | autobio | `scene` | 7 |
| `033` | `autobio_scene_insert_centrifuge_5430` | autobio | `scene` | 7 |
| `034` | `autobio_scene_lab` | autobio | `scene` | 7 |
| `035` | `autobio_scene_lab_screw_all` | autobio | `scene` | 7 |
| `036` | `autobio_scene_lab_screw_tighten` | autobio | `scene` | 7 |
| `037` | `autobio_scene_mani_centrifuge_5430` | autobio | `scene` | 7 |
| `038` | `autobio_scene_mani_centrifuge_5910` | autobio | `scene` | 7 |
| `039` | `autobio_scene_mani_centrifuge_mini` | autobio | `scene` | 7 |
| `040` | `autobio_scene_mani_pipette` | autobio | `scene` | 7 |
| `041` | `autobio_scene_mani_thermal_cycler` | autobio | `scene` | 7 |
| `042` | `autobio_scene_mani_thermal_mixer` | autobio | `scene` | 7 |
| `043` | `autobio_scene_pickup` | autobio | `scene` | 7 |
| `044` | `autobio_scene_screw` | autobio | `scene` | 7 |
| `045` | `autobio_scene_screw_test` | autobio | `scene` | 7 |
| `046` | `autobio_scene_screw_v3` | autobio | `scene` | 7 |
| `047` | `autobio_scene_vortex_mixer` | autobio | `scene` | 7 |
| `048` | `labutopia_scene_lab_001` | labutopia | `scene` | 7 |
| `049` | `labutopia_scene_lab_003` | labutopia | `scene` | 7 |
| `050` | `labutopia_scene_scene1_hard` | labutopia | `scene` | 7 |
| `051` | `labutopia_scene_clock` | labutopia | `scene` | 7 |
| `052` | `labutopia_scene_navigation_lab_01` | labutopia | `scene` | 7 |
