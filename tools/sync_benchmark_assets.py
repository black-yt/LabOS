#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "data" / "benchmark_assets"
FILES_ROOT = OUTPUT_ROOT / "files"
AUTOBIO_SOURCE_ROOT = Path(
    "/mnt/d/xwh/ailab记录/工作/26年04月/robot/AutoBio/autobio"
)
PROTO_INPUT = REPO_ROOT / "data" / "protocol_v1" / "protocol_min_v1.jsonl"
LABUTOPIA_REPO = "Rui-li023/LabUtopia"
LABUTOPIA_TREE_API = (
    "https://api.github.com/repos/Rui-li023/LabUtopia/git/trees/main?recursive=1"
)

AUTOBIO_COPY_PREFIXES = [
    "assets",
    "model/object",
    "model/instrument",
]

LABUTOPIA_DOWNLOAD_PREFIXES = [
    "assets/chemistry_lab/lab_001",
    "assets/chemistry_lab/lab_003",
    "assets/chemistry_lab/hard_task",
    "assets/robots",
    "assets/properties.json",
]


def http_get_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": "LabOS asset sync"})
    with urlopen(request) as response:
        return json.load(response)


def download_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "LabOS asset sync"})
    with urlopen(request) as response:
        return response.read()


def media_url(repo: str, path: str) -> str:
    return f"https://media.githubusercontent.com/media/{repo}/main/{quote(path)}"


def raw_url(repo: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/main/{path}"


def blob_url(repo: str, path: str) -> str:
    return f"https://github.com/{repo}/blob/main/{path}"


def tree_url(repo: str, path: str) -> str:
    return f"https://github.com/{repo}/tree/main/{path}"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def relative_to_repo(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("μ", "u").replace("µ", "u")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def alias_pattern(alias: str) -> re.Pattern[str]:
    normalized = normalize_text(alias)
    escaped = re.escape(normalized).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


MATCH_GROUPS = [
    {
        "group_id": "cell_dish",
        "aliases": [
            "cell dish",
            "cell dishes",
            "cell culture dish",
            "cell culture dishes",
            "culture dish",
            "culture dishes",
            "petri dish",
            "petri dishes",
        ],
    },
    {
        "group_id": "microcentrifuge_tube_1_5ml",
        "aliases": [
            "microcentrifuge tube",
            "microcentrifuge tubes",
            "eppendorf tube",
            "eppendorf tubes",
            "1.5 ml tube",
            "1.5 ml tubes",
            "1.5 ml microcentrifuge tube",
            "1.5 ml centrifuge tube",
            "1.5 ml screw cap tube",
        ],
    },
    {
        "group_id": "centrifuge_tube_10ml",
        "aliases": [
            "10 ml centrifuge tube",
            "10 ml centrifuge tubes",
            "10ml centrifuge tube",
            "10 ml tube",
            "10 ml tubes",
        ],
    },
    {
        "group_id": "centrifuge_tube_15ml",
        "aliases": [
            "15 ml centrifuge tube",
            "15 ml centrifuge tubes",
            "15ml centrifuge tube",
            "15 ml conical tube",
            "15 ml conical tubes",
            "15ml conical tube",
            "15 ml falcon tube",
            "15 ml falcon tubes",
        ],
    },
    {
        "group_id": "centrifuge_tube_50ml",
        "aliases": [
            "50 ml centrifuge tube",
            "50 ml centrifuge tubes",
            "50ml centrifuge tube",
            "50 ml conical tube",
            "50 ml conical tubes",
            "50ml conical tube",
            "50 ml falcon tube",
            "50 ml falcon tubes",
            "falcon tube",
            "falcon tubes",
        ],
    },
    {
        "group_id": "cryovial",
        "aliases": [
            "cryovial",
            "cryovials",
            "cryo vial",
            "cryo vials",
            "cryogenic vial",
            "cryogenic vials",
        ],
    },
    {
        "group_id": "pcr_plate",
        "aliases": [
            "pcr plate",
            "pcr plates",
            "96 well pcr plate",
            "96 well pcr plates",
            "96 well plate",
            "96 well plates",
            "96 well microplate",
            "96 well microplates",
        ],
    },
    {
        "group_id": "pipette_tip",
        "aliases": [
            "pipette tip",
            "pipette tips",
            "micropipette tip",
            "micropipette tips",
            "200 ul tip",
            "200 ul tips",
            "200 ul pipette tip",
            "200 ul pipette tips",
        ],
    },
    {
        "group_id": "pipette",
        "aliases": [
            "pipette",
            "pipettes",
            "micropipette",
            "micropipettes",
            "single channel pipette",
            "single channel pipettes",
        ],
    },
    {
        "group_id": "tip_box",
        "aliases": [
            "tip box",
            "tip boxes",
            "pipette tip box",
            "pipette tip boxes",
        ],
    },
    {
        "group_id": "pipette_rack",
        "aliases": [
            "pipette rack",
            "pipette racks",
            "pipette holder",
            "pipette holders",
            "pipette stand",
            "pipette stands",
        ],
    },
    {
        "group_id": "tube_rack",
        "aliases": [
            "tube rack",
            "tube racks",
            "centrifuge tube rack",
            "centrifuge tube racks",
            "microcentrifuge tube rack",
            "microcentrifuge tube racks",
            "test tube rack",
            "test tube racks",
        ],
    },
    {
        "group_id": "centrifuge",
        "aliases": [
            "centrifuge",
            "centrifuges",
            "microcentrifuge",
            "microcentrifuges",
            "bench centrifuge",
            "bench centrifuges",
            "refrigerated centrifuge",
            "refrigerated centrifuges",
        ],
    },
    {
        "group_id": "thermal_cycler",
        "aliases": [
            "thermal cycler",
            "thermal cyclers",
            "thermocycler",
            "thermocyclers",
            "pcr machine",
            "pcr machines",
        ],
    },
    {
        "group_id": "thermal_mixer",
        "aliases": [
            "thermal mixer",
            "thermal mixers",
            "thermomixer",
            "thermomixers",
            "heat shaker",
            "heat shakers",
        ],
    },
    {
        "group_id": "vortex_mixer",
        "aliases": [
            "vortex mixer",
            "vortex mixers",
            "vortexer",
            "vortexers",
            "vortex genie",
        ],
    },
    {
        "group_id": "beaker",
        "aliases": [
            "beaker",
            "beakers",
            "glass beaker",
            "glass beakers",
        ],
    },
    {
        "group_id": "conical_bottle",
        "aliases": [
            "conical bottle",
            "conical bottles",
            "erlenmeyer flask",
            "erlenmeyer flasks",
            "conical flask",
            "conical flasks",
        ],
    },
    {
        "group_id": "graduated_cylinder",
        "aliases": [
            "graduated cylinder",
            "graduated cylinders",
            "measuring cylinder",
            "measuring cylinders",
        ],
    },
    {
        "group_id": "glass_rod",
        "aliases": [
            "glass rod",
            "glass rods",
            "stirring rod",
            "stirring rods",
            "glass stirring rod",
            "glass stirring rods",
        ],
    },
    {
        "group_id": "drying_box",
        "aliases": [
            "drying box",
            "drying boxes",
            "dry box",
            "dry boxes",
            "drying oven",
            "drying ovens",
            "drying chamber",
            "drying chambers",
        ],
    },
    {
        "group_id": "heating_device",
        "aliases": [
            "hot plate",
            "hot plates",
            "heating plate",
            "heating plates",
            "heating device",
            "heating devices",
            "heat device",
            "heat devices",
            "heater",
            "heaters",
        ],
    },
    {
        "group_id": "muffle_furnace",
        "aliases": [
            "muffle furnace",
            "muffle furnaces",
            "laboratory furnace",
            "laboratory furnaces",
        ],
    },
]

GROUP_TO_ALIASES = {
    item["group_id"]: item["aliases"] for item in MATCH_GROUPS
}
GROUP_TO_PATTERNS = {
    item["group_id"]: [alias_pattern(alias) for alias in item["aliases"]]
    for item in MATCH_GROUPS
}


CATALOG_ENTRIES = [
    {
        "asset_id": "autobio_cell_dish_100",
        "asset_name": "100 mm Cell Dish",
        "match_group": "cell_dish",
        "aliases": GROUP_TO_ALIASES["cell_dish"],
        "purpose": "Cell culture plate for seeding, incubation, washing, and imaging.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/cell_dish_100_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/cell_dish_100_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_1_5ml_screw",
        "asset_name": "1.5 mL Screw-Cap Microcentrifuge Tube",
        "match_group": "microcentrifuge_tube_1_5ml",
        "aliases": GROUP_TO_ALIASES["microcentrifuge_tube_1_5ml"],
        "purpose": "Small sample tube for aliquoting, mixing, incubation, and centrifugation.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/centrifuge_1-5ml_screw_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/centrifuge_1-5ml_screw_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_10ml",
        "asset_name": "10 mL Centrifuge Tube",
        "match_group": "centrifuge_tube_10ml",
        "aliases": GROUP_TO_ALIASES["centrifuge_tube_10ml"],
        "purpose": "Medium-volume sample tube for transfer and centrifugation.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/centrifuge_10ml_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/centrifuge_10ml_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_1500ul_open",
        "asset_name": "1.5 mL Open Microcentrifuge Tube",
        "match_group": "microcentrifuge_tube_1_5ml",
        "aliases": GROUP_TO_ALIASES["microcentrifuge_tube_1_5ml"],
        "purpose": "Open microcentrifuge tube for liquid handling and insertion tasks.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/centrifuge_1500ul_no_lid_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/centrifuge_1500ul_no_lid_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_15ml_screw",
        "asset_name": "15 mL Screw-Cap Centrifuge Tube",
        "match_group": "centrifuge_tube_15ml",
        "aliases": GROUP_TO_ALIASES["centrifuge_tube_15ml"],
        "purpose": "Conical sample tube for medium-volume transfer and centrifugation.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/centrifuge_15ml_screw_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/centrifuge_15ml_screw_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_50ml",
        "asset_name": "50 mL Centrifuge Tube",
        "match_group": "centrifuge_tube_50ml",
        "aliases": GROUP_TO_ALIASES["centrifuge_tube_50ml"],
        "purpose": "Large conical tube for reagent preparation and centrifugation.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/centrifuge_50ml_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/centrifuge_50ml_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_50ml_screw",
        "asset_name": "50 mL Screw-Cap Centrifuge Tube",
        "match_group": "centrifuge_tube_50ml",
        "aliases": GROUP_TO_ALIASES["centrifuge_tube_50ml"],
        "purpose": "Large screw-cap tube for sealed transfer and centrifugation.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/centrifuge_50ml_screw_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/centrifuge_50ml_screw_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_cryovial_1_8ml",
        "asset_name": "1.8 mL Cryovial",
        "match_group": "cryovial",
        "aliases": GROUP_TO_ALIASES["cryovial"],
        "purpose": "Cryogenic storage vial for frozen samples and aliquots.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/cryovial_1-8ml_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/cryovial_1-8ml_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_pcr_plate_96well",
        "asset_name": "96-Well PCR Plate",
        "match_group": "pcr_plate",
        "aliases": GROUP_TO_ALIASES["pcr_plate"],
        "purpose": "Plate for PCR setup, thermal cycling, and sample organization.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/pcr_plate_96well_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/pcr_plate_96well_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_tip_200ul",
        "asset_name": "200 uL Pipette Tip",
        "match_group": "pipette_tip",
        "aliases": GROUP_TO_ALIASES["pipette_tip"],
        "purpose": "Disposable liquid-handling tip for pipetting small volumes.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/container/tip_200ul_vis/visual.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": tree_url(
            "autobio-bench/AutoBio",
            "autobio/assets/container/tip_200ul_vis",
        ),
    },
    {
        "asset_id": "autobio_pipette",
        "asset_name": "Micropipette",
        "match_group": "pipette",
        "aliases": GROUP_TO_ALIASES["pipette"],
        "purpose": "Manual pipette for aspirating and dispensing liquids.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/model/object/pipette.gen.xml",
        "source_project": "autobio",
        "render_status": "ready_mjcf_package",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/model/object/pipette.gen.xml",
        ),
    },
    {
        "asset_id": "autobio_tip_box_24slot",
        "asset_name": "24-Slot Tip Box",
        "match_group": "tip_box",
        "aliases": GROUP_TO_ALIASES["tip_box"],
        "purpose": "Container for storing and presenting pipette tips.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/rack/tip_box_24slot_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/rack/tip_box_24slot_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_pipette_rack_tri",
        "asset_name": "Triangular Pipette Rack",
        "match_group": "pipette_rack",
        "aliases": GROUP_TO_ALIASES["pipette_rack"],
        "purpose": "Rack for holding pipettes upright between operations.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/rack/pipette_rack_tri_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/rack/pipette_rack_tri_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_10slot_rack",
        "asset_name": "10-Slot Centrifuge Tube Rack",
        "match_group": "tube_rack",
        "aliases": GROUP_TO_ALIASES["tube_rack"],
        "purpose": "Rack for organizing and positioning sample tubes.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/rack/centrifuge_10slot_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/rack/centrifuge_10slot_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_plate_60well",
        "asset_name": "60-Well Plate Rack",
        "match_group": "tube_rack",
        "aliases": GROUP_TO_ALIASES["tube_rack"],
        "purpose": "Multi-well rack for arranging small tubes or vials.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/assets/rack/centrifuge_plate_60well_vis.obj",
        "source_project": "autobio",
        "render_status": "ready_obj",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/assets/rack/centrifuge_plate_60well_vis.obj",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_5430",
        "asset_name": "Eppendorf 5430 Centrifuge",
        "match_group": "centrifuge",
        "aliases": GROUP_TO_ALIASES["centrifuge"],
        "purpose": "Bench centrifuge for spinning small sample tubes.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/model/instrument/centrifuge_eppendorf_5430.xml",
        "source_project": "autobio",
        "render_status": "ready_mjcf_package",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/model/instrument/centrifuge_eppendorf_5430.xml",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_5910_ri",
        "asset_name": "Eppendorf 5910 Ri Centrifuge",
        "match_group": "centrifuge",
        "aliases": GROUP_TO_ALIASES["centrifuge"],
        "purpose": "Large refrigerated centrifuge for higher-volume tube spinning.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/model/instrument/centrifuge_eppendorf_5910_ri.xml",
        "source_project": "autobio",
        "render_status": "ready_mjcf_package",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/model/instrument/centrifuge_eppendorf_5910_ri.xml",
        ),
    },
    {
        "asset_id": "autobio_centrifuge_tgear_mini",
        "asset_name": "Tiangen Tgear Mini Centrifuge",
        "match_group": "centrifuge",
        "aliases": GROUP_TO_ALIASES["centrifuge"],
        "purpose": "Compact mini centrifuge for quick spin-down operations.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/model/instrument/centrifuge_tiangen_tgear_mini.xml",
        "source_project": "autobio",
        "render_status": "ready_mjcf_package",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/model/instrument/centrifuge_tiangen_tgear_mini.xml",
        ),
    },
    {
        "asset_id": "autobio_thermal_cycler_c1000",
        "asset_name": "Bio-Rad C1000 Thermal Cycler",
        "match_group": "thermal_cycler",
        "aliases": GROUP_TO_ALIASES["thermal_cycler"],
        "purpose": "PCR instrument for running thermal cycling programs.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/model/instrument/thermal_cycler_biorad_c1000.xml",
        "source_project": "autobio",
        "render_status": "ready_mjcf_package",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/model/instrument/thermal_cycler_biorad_c1000.xml",
        ),
    },
    {
        "asset_id": "autobio_thermal_mixer_eppendorf_c",
        "asset_name": "Eppendorf C Thermal Mixer",
        "match_group": "thermal_mixer",
        "aliases": GROUP_TO_ALIASES["thermal_mixer"],
        "purpose": "Instrument for controlled heating and shaking of samples.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/model/instrument/thermal_mixer_eppendorf_c.xml",
        "source_project": "autobio",
        "render_status": "ready_mjcf_package",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/model/instrument/thermal_mixer_eppendorf_c.xml",
        ),
    },
    {
        "asset_id": "autobio_vortex_mixer_genie_2",
        "asset_name": "Genie 2 Vortex Mixer",
        "match_group": "vortex_mixer",
        "aliases": GROUP_TO_ALIASES["vortex_mixer"],
        "purpose": "Mixer for vortexing tubes and suspensions.",
        "local_relative_path": "data/benchmark_assets/files/autobio/autobio/model/instrument/vortex_mixer_genie_2.xml",
        "source_project": "autobio",
        "render_status": "ready_mjcf_package",
        "original_url": raw_url(
            "autobio-bench/AutoBio",
            "autobio/model/instrument/vortex_mixer_genie_2.xml",
        ),
    },
    {
        "asset_id": "labutopia_beaker_family",
        "asset_name": "Beaker Family",
        "match_group": "beaker",
        "aliases": GROUP_TO_ALIASES["beaker"],
        "purpose": "General glass container for mixing, pouring, heating, and transfer.",
        "local_relative_path": "data/benchmark_assets/files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd#/World/beaker",
        "source_project": "labutopia",
        "render_status": "downloaded_usd_requires_conversion",
        "original_url": media_url(
            LABUTOPIA_REPO,
            "assets/chemistry_lab/lab_001/lab_001.usd",
        ),
    },
    {
        "asset_id": "labutopia_conical_bottle_family",
        "asset_name": "Conical Bottle / Flask Family",
        "match_group": "conical_bottle",
        "aliases": GROUP_TO_ALIASES["conical_bottle"],
        "purpose": "Flask-style glassware for liquid storage, mixing, and pouring.",
        "local_relative_path": "data/benchmark_assets/files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd#/World/conical_bottle02",
        "source_project": "labutopia",
        "render_status": "downloaded_usd_requires_conversion",
        "original_url": media_url(
            LABUTOPIA_REPO,
            "assets/chemistry_lab/lab_001/lab_001.usd",
        ),
    },
    {
        "asset_id": "labutopia_graduated_cylinder_03",
        "asset_name": "Graduated Cylinder",
        "match_group": "graduated_cylinder",
        "aliases": GROUP_TO_ALIASES["graduated_cylinder"],
        "purpose": "Volumetric cylinder for measuring and dispensing liquids.",
        "local_relative_path": "data/benchmark_assets/files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd#/World/graduated_cylinder_03",
        "source_project": "labutopia",
        "render_status": "downloaded_usd_requires_conversion",
        "original_url": media_url(
            LABUTOPIA_REPO,
            "assets/chemistry_lab/lab_001/lab_001.usd",
        ),
    },
    {
        "asset_id": "labutopia_glass_rod",
        "asset_name": "Glass Rod",
        "match_group": "glass_rod",
        "aliases": GROUP_TO_ALIASES["glass_rod"],
        "purpose": "Rod for manual stirring and mixing.",
        "local_relative_path": "data/benchmark_assets/files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd#/World/glass_rod",
        "source_project": "labutopia",
        "render_status": "downloaded_usd_requires_conversion",
        "original_url": media_url(
            LABUTOPIA_REPO,
            "assets/chemistry_lab/lab_003/lab_003.usd",
        ),
    },
    {
        "asset_id": "labutopia_test_tube_rack",
        "asset_name": "Test Tube Rack",
        "match_group": "tube_rack",
        "aliases": GROUP_TO_ALIASES["tube_rack"],
        "purpose": "Rack for holding tubes upright during preparation and storage.",
        "local_relative_path": "data/benchmark_assets/files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd#/World/test_tube_rack",
        "source_project": "labutopia",
        "render_status": "downloaded_usd_requires_conversion",
        "original_url": media_url(
            LABUTOPIA_REPO,
            "assets/chemistry_lab/lab_001/lab_001.usd",
        ),
    },
    {
        "asset_id": "labutopia_drying_box_family",
        "asset_name": "Drying Box Family",
        "match_group": "drying_box",
        "aliases": GROUP_TO_ALIASES["drying_box"],
        "purpose": "Device used for drying or enclosed heating workflows.",
        "local_relative_path": "data/benchmark_assets/files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd#/World/DryingBox_01",
        "source_project": "labutopia",
        "render_status": "downloaded_usd_requires_conversion",
        "original_url": media_url(
            LABUTOPIA_REPO,
            "assets/chemistry_lab/lab_001/lab_001.usd",
        ),
    },
    {
        "asset_id": "labutopia_heat_device",
        "asset_name": "Heat Device / Hot Plate",
        "match_group": "heating_device",
        "aliases": GROUP_TO_ALIASES["heating_device"],
        "purpose": "Heating surface or device used to activate thermal tasks.",
        "local_relative_path": "data/benchmark_assets/files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd#/World/heat_device",
        "source_project": "labutopia",
        "render_status": "downloaded_usd_requires_conversion",
        "original_url": media_url(
            LABUTOPIA_REPO,
            "assets/chemistry_lab/lab_003/lab_003.usd",
        ),
    },
    {
        "asset_id": "labutopia_muffle_furnace",
        "asset_name": "Muffle Furnace",
        "match_group": "muffle_furnace",
        "aliases": GROUP_TO_ALIASES["muffle_furnace"],
        "purpose": "High-temperature heating device for enclosed furnace operations.",
        "local_relative_path": "data/benchmark_assets/files/labutopia/assets/chemistry_lab/hard_task/Scene1_hard.usd#/World/MuffleFurnace",
        "source_project": "labutopia",
        "render_status": "downloaded_usd_requires_conversion",
        "original_url": media_url(
            LABUTOPIA_REPO,
            "assets/chemistry_lab/hard_task/Scene1_hard.usd",
        ),
    },
]

for item in CATALOG_ENTRIES:
    if item["source_project"] == "labutopia":
        item["reference_kind"] = "scene_prim_reference"
    elif item["render_status"] == "ready_obj":
        item["reference_kind"] = "standalone_mesh_root"
    else:
        item["reference_kind"] = "package_entrypoint"


ENTRY_TYPE_LABELS = {
    "standalone_mesh_root": "asset (standalone_mesh_root)",
    "package_entrypoint": "composite asset (package_entrypoint)",
    "scene_prim_reference": "scene object reference (scene_prim_reference)",
}


def catalog_for_markdown(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Merged Benchmark Asset Catalog",
        "",
        "| Asset Name | Match Group | Aliases | Purpose | Local Relative Path | Source Project | Entry Type | Render Status | Original URL |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for item in entries:
        aliases = ", ".join(item["aliases"])
        original_url = f"[link]({item['original_url']})"
        row = [
            item["asset_name"],
            item["match_group"],
            aliases,
            item["purpose"],
            item["local_relative_path"],
            item["source_project"],
            ENTRY_TYPE_LABELS[item["reference_kind"]],
            item["render_status"],
            original_url,
        ]
        row = [cell.replace("|", r"\|") for cell in row]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)


def sync_autobio(force: bool) -> None:
    autobio_out = FILES_ROOT / "autobio" / "autobio"
    for prefix in AUTOBIO_COPY_PREFIXES:
        src = AUTOBIO_SOURCE_ROOT / prefix
        dst = autobio_out / prefix
        if src.is_dir():
            if dst.exists() and force:
                shutil.rmtree(dst)
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            ensure_parent(dst)
            shutil.copy2(src, dst)


def list_labutopia_files(prefixes: list[str]) -> list[str]:
    tree = http_get_json(LABUTOPIA_TREE_API)["tree"]
    paths = []
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item["path"]
        if any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes):
            paths.append(path)
    return sorted(paths)


def sync_labutopia(force: bool) -> list[str]:
    paths = list_labutopia_files(LABUTOPIA_DOWNLOAD_PREFIXES)
    for path in paths:
        dst = FILES_ROOT / "labutopia" / Path(path)
        if dst.exists() and not force:
            continue
        ensure_parent(dst)
        dst.write_bytes(download_bytes(media_url(LABUTOPIA_REPO, path)))
    return paths


def write_catalog(entries: list[dict[str, Any]]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "merged_asset_catalog.json").write_text(
        json.dumps(entries, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "merged_asset_catalog.md").write_text(
        catalog_for_markdown(entries),
        encoding="utf-8",
    )


def iter_protocols(path: Path) -> list[dict[str, Any]]:
    protocols = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            protocols.append(json.loads(line))
    return protocols


def protocol_corpus(protocol: dict[str, Any]) -> str:
    chunks: list[str] = [protocol.get("title", ""), protocol.get("background", "")]
    materials = protocol.get("materials", {})
    for kind in ("equipment", "reagents"):
        for item in materials.get(kind, []):
            if isinstance(item, dict):
                chunks.append(item.get("name", ""))
            elif isinstance(item, str):
                chunks.append(item)
    for step in protocol.get("procedure", []):
        if isinstance(step, dict):
            chunks.append(step.get("stage", ""))
            chunks.append(step.get("description", ""))
        elif isinstance(step, str):
            chunks.append(step)
    return normalize_text(" ".join(chunks))


def match_protocols(
    entries: list[dict[str, Any]],
    protocol_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    protocols = iter_protocols(protocol_path)
    matchable_groups = sorted({item["match_group"] for item in entries})
    entries_by_group: dict[str, list[dict[str, Any]]] = {}
    for item in entries:
        entries_by_group.setdefault(item["match_group"], []).append(item)

    matched = []
    hit_counts = {group: 0 for group in matchable_groups}
    for protocol in protocols:
        corpus = protocol_corpus(protocol)
        matched_groups = []
        for group_id in matchable_groups:
            if any(pattern.search(corpus) for pattern in GROUP_TO_PATTERNS[group_id]):
                matched_groups.append(group_id)
        if not matched_groups:
            continue

        for group_id in matched_groups:
            hit_counts[group_id] += 1

        candidate_assets = []
        seen_ids = set()
        for group_id in matched_groups:
            for asset in entries_by_group[group_id]:
                if asset["asset_id"] in seen_ids:
                    continue
                candidate_assets.append(
                    {
                        "asset_id": asset["asset_id"],
                        "asset_name": asset["asset_name"],
                        "source_project": asset["source_project"],
                        "local_relative_path": asset["local_relative_path"],
                        "match_group": asset["match_group"],
                    }
                )
                seen_ids.add(asset["asset_id"])

        enriched = dict(protocol)
        enriched["matched_groups"] = matched_groups
        enriched["candidate_assets"] = candidate_assets
        matched.append(enriched)

    stats = {
        "protocol_input": relative_to_repo(protocol_path),
        "catalog_size": len(entries),
        "match_group_count": len(matchable_groups),
        "protocol_count": len(protocols),
        "matched_protocol_count": len(matched),
        "unmatched_protocol_count": len(protocols) - len(matched),
        "hit_counts": hit_counts,
    }
    return matched, stats


def write_matches(matches: list[dict[str, Any]], stats: dict[str, Any]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    match_path = OUTPUT_ROOT / "protocol_min_v1_with_assets.jsonl"
    with match_path.open("w", encoding="utf-8") as handle:
        for row in matches:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary_path = OUTPUT_ROOT / "protocol_min_v1_asset_matches.jsonl"
    with summary_path.open("w", encoding="utf-8") as handle:
        for row in matches:
            slim = {
                "id": row["id"],
                "title": row.get("title", ""),
                "matched_groups": row["matched_groups"],
                "candidate_asset_ids": [
                    item["asset_id"] for item in row["candidate_assets"]
                ],
            }
            handle.write(json.dumps(slim, ensure_ascii=False) + "\n")

    (OUTPUT_ROOT / "protocol_min_v1_asset_matches.stats.json").write_text(
        json.dumps(stats, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync benchmark assets and match protocol_min_v1 against them."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-copy and re-download assets even if target files already exist.",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip asset copy/download and only rewrite catalog + protocol matches.",
    )
    args = parser.parse_args()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    if not args.skip_sync:
        if not AUTOBIO_SOURCE_ROOT.exists():
            raise FileNotFoundError(
                f"AutoBio source root not found: {AUTOBIO_SOURCE_ROOT}"
            )
        sync_autobio(force=args.force)
        downloaded = sync_labutopia(force=args.force)
        print(f"Downloaded {len(downloaded)} LabUtopia files.")

    write_catalog(CATALOG_ENTRIES)
    matches, stats = match_protocols(CATALOG_ENTRIES, PROTO_INPUT)
    write_matches(matches, stats)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
