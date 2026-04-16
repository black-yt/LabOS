import * as THREE from "https://unpkg.com/three@0.168.0/build/three.module.js";
import { OrbitControls } from "https://unpkg.com/three@0.168.0/examples/jsm/controls/OrbitControls.js";
import { OBJLoader } from "https://unpkg.com/three@0.168.0/examples/jsm/loaders/OBJLoader.js";
import { STLLoader } from "https://unpkg.com/three@0.168.0/examples/jsm/loaders/STLLoader.js";

const MODEL_LIBRARY = {
  thermalCycler: {
    label: "Thermal cycler / Bio-Rad C1000",
    description:
      "Composite OBJ assembly copied from AutoBio visual meshes. Used here as the anchor asset for thermal cycling and PCR planning examples.",
    parts: [
      ["assets/models/thermal_cycler/body-visual-0.obj", "#d7cfb6"],
      ["assets/models/thermal_cycler/body-visual-1.obj", "#b8b29e"],
      ["assets/models/thermal_cycler/body-visual-2.obj", "#d5ccb0"],
      ["assets/models/thermal_cycler/body-visual-3.obj", "#857e6d"],
      ["assets/models/thermal_cycler/lid-visual-0.obj", "#cbc29f"],
      ["assets/models/thermal_cycler/lid-visual-1.obj", "#706c61"],
      ["assets/models/thermal_cycler/lid-lever-visual-0.obj", "#3b3b3b"],
      ["assets/models/thermal_cycler/lid-lever-visual-1.obj", "#3b3b3b"],
      ["assets/models/thermal_cycler/lid-force-knob-visual-0.obj", "#00c2a8"],
      ["assets/models/thermal_cycler/reaction-block-visual-0.obj", "#5d5d66"],
    ],
    rotation: [-Math.PI / 2, 0, Math.PI],
    targetSize: 3.4,
    tags: ["AutoBio asset", "OBJ assembly", "PCR device"],
  },
  centrifugeMini: {
    label: "Mini centrifuge / Tiangen Tgear",
    description:
      "Composite OBJ assembly for a desktop centrifuge. The lid and rotor are separated so the page can tie visual questions to embodied lid-closing tasks.",
    parts: [
      ["assets/models/centrifuge_mini/body-visual-0.obj", "#262626"],
      ["assets/models/centrifuge_mini/body-visual-1.obj", "#f0dd34"],
      ["assets/models/centrifuge_mini/body-visual-2.obj", "#232323"],
      ["assets/models/centrifuge_mini/body-visual-3.obj", "#3a3a3a"],
      ["assets/models/centrifuge_mini/body-visual-4.obj", "#f0dd34"],
      ["assets/models/centrifuge_mini/lid-visual-0.obj", "#292929"],
      ["assets/models/centrifuge_mini/rotor-visual-0.obj", "#101010"],
    ],
    rotation: [-Math.PI / 2, 0, Math.PI],
    targetSize: 3.2,
    tags: ["AutoBio asset", "OBJ assembly", "Rotor / lid task"],
  },
  thermalMixer: {
    label: "Thermal mixer / Eppendorf C",
    description:
      "Composite OBJ assembly with a control panel region, useful for linking planning output to a constrained action pool of mixer operations.",
    parts: [
      ["assets/models/thermal_mixer/body-visual-0.obj", "#c8c2ad"],
      ["assets/models/thermal_mixer/body-visual-1.obj", "#2f2f2f"],
      ["assets/models/thermal_mixer/body-visual-2.obj", "#c8c2ad"],
      ["assets/models/thermal_mixer/body-visual-3.obj", "#395e94"],
      ["assets/models/thermal_mixer/body-visual-4.obj", "#969184"],
    ],
    rotation: [-Math.PI / 2, 0, Math.PI],
    targetSize: 3.1,
    tags: ["AutoBio asset", "OBJ assembly", "Panel control task"],
  },
  vortexMixer: {
    label: "Vortex mixer / Genie 2",
    description:
      "Composite OBJ assembly with platform, switch, and knob. This is used for asset understanding examples and planning constraints around agitation actions.",
    parts: [
      ["assets/models/vortex_mixer/body-visual-0.obj", "#1c1c1c"],
      ["assets/models/vortex_mixer/body-visual-1.obj", "#f5d81c"],
      ["assets/models/vortex_mixer/body-visual-2.obj", "#4b4a44"],
      ["assets/models/vortex_mixer/knob-visual-0.obj", "#161616"],
      ["assets/models/vortex_mixer/platform-visual-0.obj", "#111111"],
      ["assets/models/vortex_mixer/switch-visual-0.obj", "#b7ff39"],
    ],
    rotation: [-Math.PI / 2, 0, Math.PI],
    targetSize: 3.2,
    tags: ["AutoBio asset", "OBJ assembly", "Mixing / agitation"],
  },
  tube15ml: {
    label: "15 mL centrifuge tube",
    description:
      "Two-piece STL assembly of a 15 mL screw-cap tube. The page uses it as a light-weight object for planning and sim2real transfer items.",
    stl: [
      ["assets/models/tube_15ml/centrifuge_tube_15ml_body.STL", "#d1e95a"],
      ["assets/models/tube_15ml/centrifuge_tube_15ml_cap.STL", "#cdd0d4"],
    ],
    rotation: [-Math.PI / 2, 0, Math.PI],
    targetSize: 2.7,
    tags: ["AutoBio asset", "STL assembly", "Tube handling"],
  },
};

const SECTIONS = [
  {
    id: "part-1",
    label: "Part 1",
    navTitle: "Experimental Asset Understanding",
    navMeta: "2 MCQ items with 3D instruments",
    kicker: "Part 1 · Visual use understanding",
    title: "Experimental Asset Understanding",
    summary:
      "Instrument-centric multiple-choice probes grounded in Nature Protocols semantics and anchored to AutoBio / LabUtopia asset families.",
    items: [
      {
        id: "asset-q1",
        title: "Thermal cycler lid control",
        kind: "MCQ sample",
        modelKey: "thermalCycler",
        imageSrc: "assets/thermal_cycler.png",
        videoSrc: null,
        cardSummary:
          "A control-state item that asks whether the operator identifies the heated-lid closure requirement before cycling begins.",
        prompt:
          "A PCR preparation workflow is about to start. Looking at the thermal cycler and its lid assembly, which control or state transition must happen before thermocycling can run safely?",
        options: [
          ["A", "Open the block and remove the reaction plate once the display powers on."],
          ["B", "Close and secure the lid so the heated top can press the plate during cycling."],
          ["C", "Switch the cooling fan off and leave the lid lever floating above the block."],
          ["D", "Keep the lid open and only set the denaturation temperature."],
        ],
        answer:
          "B. Nature Protocols-style PCR workflows require the reaction vessel to be seated and the lid secured before a cycle starts. This also aligns with AutoBio's thermal cycler open/close asset family.",
        notes: [
          "Scientific grounding: PCR protocols depend on stable heated-lid pressure to avoid condensation.",
          "Embodied alignment: the same asset family appears in AutoBio as a lid manipulation task.",
        ],
      },
      {
        id: "asset-q2",
        title: "Mini centrifuge rotor semantics",
        kind: "MCQ sample",
        modelKey: "centrifugeMini",
        imageSrc: "assets/centrifuge_mini.png",
        videoSrc: null,
        cardSummary:
          "A state-and-part question about distinguishing the rotor cavity from unrelated housing surfaces in a desktop centrifuge.",
        prompt:
          "The mini centrifuge is shown with its central black circular module visible. Which statement best describes the function of that module in the experiment workflow?",
        options: [
          ["A", "It is the imaging sensor used to read barcoded samples before spin."],
          ["B", "It is the rotor seat that holds tubes in balanced positions during spinning."],
          ["C", "It is a waste reservoir where supernatant is discarded after separation."],
          ["D", "It is the heated block used for thermocycling amplification."],
        ],
        answer:
          "B. The visible central module is the rotor region. Correctly identifying this matters because later planning and transfer tasks depend on whether the model understands tube placement, balancing, and lid closure.",
        notes: [
          "Scientific grounding: centrifugation steps in wet-lab protocols require balanced tube placement.",
          "Embodied alignment: AutoBio already exposes lid and rotor-loading tasks for centrifuge assets.",
        ],
      },
    ],
  },
  {
    id: "part-2",
    label: "Part 2",
    navTitle: "Long-Horizon Planning",
    navMeta: "2 constrained protocol programs",
    kicker: "Part 2 · Constrained long program synthesis",
    title: "Long-Horizon Planning",
    summary:
      "Protocol planning explicitly follows the SGI-WetExperiment pattern: the input includes a finite action pool and the output is a Python action program that can be parsed with the Python AST.",
    items: [
      {
        id: "plan-q1",
        title: "qPCR preparation under constrained actions",
        kind: "Planning sample",
        modelKey: "thermalCycler",
        imageSrc: "assets/thermal_cycler.png",
        videoSrc: null,
        cardSummary:
          "A scaffolded planning item with a thermal-cycler-centric action pool and a reference Python program.",
        prompt:
          "Design a long-horizon qPCR workflow for cytokine-response quantification. The model receives the experiment description, reagent list, equipment list, and the finite action pool below. The target output is a Python action program.",
        actionPool: [
          "def aliquot_master_mix(reagent_set: str, destination_plate: str, volume_ul: int) -> str: ...",
          "def load_samples(sample_tubes: str, destination_plate: str, layout: str) -> str: ...",
          "def seal_plate(plate: str, seal_type: str) -> str: ...",
          "def place_plate_in_thermal_cycler(plate: str, instrument: str) -> str: ...",
          "def close_thermal_cycler_lid(instrument: str, pressure_mode: str) -> str: ...",
          "def set_pcr_program(instrument: str, protocol_name: str) -> str: ...",
          "def run_pcr_program(instrument: str, runtime_min: int) -> str: ...",
          "def unload_plate(instrument: str, plate: str) -> str: ...",
        ],
        referenceProgram: `qpcr_plate = aliquot_master_mix(\n    reagent_set="cytokine_qpcr_mix",\n    destination_plate="96_well_plate",\n    volume_ul=18,\n)\n\nloaded_plate = load_samples(\n    sample_tubes="stimulated_rna_samples",\n    destination_plate=qpcr_plate,\n    layout="triplicate_layout",\n)\n\nsealed_plate = seal_plate(\n    plate=loaded_plate,\n    seal_type="optical_film",\n)\n\ncycler_slot = place_plate_in_thermal_cycler(\n    plate=sealed_plate,\n    instrument="thermal_cycler_biorad_c1000",\n)\n\nlid_state = close_thermal_cycler_lid(\n    instrument="thermal_cycler_biorad_c1000",\n    pressure_mode="heated_lid_secure",\n)\n\nprogram_state = set_pcr_program(\n    instrument="thermal_cycler_biorad_c1000",\n    protocol_name="cytokine_panel_qpcr",\n)\n\nrun_state = run_pcr_program(\n    instrument="thermal_cycler_biorad_c1000",\n    runtime_min=95,\n)\n\ncompleted_plate = unload_plate(\n    instrument="thermal_cycler_biorad_c1000",\n    plate=sealed_plate,\n)`,
        scoring: [
          "AST parse success on the generated Python program.",
          "Allowed-call accuracy against the finite action pool.",
          "Argument-match accuracy for plate, instrument, seal type, and runtime.",
          "Dependency-edge accuracy from plate preparation to program execution.",
        ],
      },
      {
        id: "plan-q2",
        title: "Thermal mixer incubation and agitation chain",
        kind: "Planning sample",
        modelKey: "thermalMixer",
        imageSrc: "assets/thermal_mixer.png",
        videoSrc: null,
        cardSummary:
          "A constrained action-space item that uses mixer control actions and parameterized incubation settings.",
        prompt:
          "Plan a protein-binding incubation with timed heating, interval mixing, and post-incubation aliquoting. The model must stay inside the finite Python action pool.",
        actionPool: [
          "def load_tubes_into_mixer(tube_set: str, rack_slot: str, instrument: str) -> str: ...",
          "def lock_mixer_block(instrument: str, block_type: str) -> str: ...",
          "def set_mixer_temperature(instrument: str, target_celsius: int) -> str: ...",
          "def set_mixer_speed(instrument: str, rpm: int, mode: str) -> str: ...",
          "def set_mixer_duration(instrument: str, duration_min: int) -> str: ...",
          "def start_mixer_run(instrument: str) -> str: ...",
          "def pause_and_brief_spin(tube_set: str, spin_seconds: int) -> str: ...",
          "def collect_post_incubation_aliquot(tube_set: str, volume_ul: int, destination: str) -> str: ...",
        ],
        referenceProgram: `loaded_tubes = load_tubes_into_mixer(\n    tube_set="binding_reaction_triplicates",\n    rack_slot="thermomixer_block_a",\n    instrument="thermal_mixer_eppendorf_c",\n)\n\nblock_state = lock_mixer_block(\n    instrument="thermal_mixer_eppendorf_c",\n    block_type="1.5mL_tube_block",\n)\n\ntemp_state = set_mixer_temperature(\n    instrument="thermal_mixer_eppendorf_c",\n    target_celsius=37,\n)\n\nspeed_state = set_mixer_speed(\n    instrument="thermal_mixer_eppendorf_c",\n    rpm=900,\n    mode="interval_mix",\n)\n\nduration_state = set_mixer_duration(\n    instrument="thermal_mixer_eppendorf_c",\n    duration_min=45,\n)\n\nrun_state = start_mixer_run(\n    instrument="thermal_mixer_eppendorf_c",\n)\n\nspin_state = pause_and_brief_spin(\n    tube_set=loaded_tubes,\n    spin_seconds=8,\n)\n\naliquot_state = collect_post_incubation_aliquot(\n    tube_set=loaded_tubes,\n    volume_ul=25,\n    destination="assay_plate_b",\n)`,
        scoring: [
          "Allowed-call accuracy against the mixer-specific action pool.",
          "Argument-match accuracy for temperature, speed, duration, and aliquot volume.",
          "Length adequacy, since the answer should be a multi-step program rather than a summary.",
          "Action consistency between the thermal mixer asset and the chosen control functions.",
        ],
      },
    ],
  },
  {
    id: "part-3",
    label: "Part 3",
    navTitle: "Sim2Real Preview",
    navMeta: "2 transfer probes with clips",
    kicker: "Part 3 · Embodied transfer preview",
    title: "Sim2Real Preview",
    summary:
      "A preview lane for embodied transfer. The benchmark UI keeps it visible so the first two parts already point toward executable assets, canonical actions, and observable success conditions.",
    items: [
      {
        id: "sim-q1",
        title: "Tube pickup transfer probe",
        kind: "Transfer item",
        modelKey: "tube15ml",
        imageSrc: "assets/centrifuge_mini.png",
        videoSrc: "assets/videos/pickup_tube.mp4",
        cardSummary:
          "A pickup scenario where the policy must align gripper approach, tube orientation, and post-grasp stability.",
        prompt:
          "Observe the simulated pickup clip and rotate the 15 mL tube model. What should the sim2real evaluator check before this episode is counted as transferable to a real bench setup?",
        checks: [
          "The gripper contacts the tube body rather than clipping through the cap.",
          "The tube remains stable after lift-off instead of oscillating or slipping.",
          "The post-grasp orientation remains compatible with downstream transfer or loading steps.",
          "The success event is tied to the tube pose, not just the arm trajectory.",
        ],
        answer:
          "A valid transfer probe should score grasp stability, pose consistency, and downstream usability. A pure end-effector match is not enough if the real tube would slip or become unusable for the next protocol step.",
      },
      {
        id: "sim-q2",
        title: "Mini centrifuge lid closure probe",
        kind: "Transfer item",
        modelKey: "centrifugeMini",
        imageSrc: "assets/centrifuge_mini.png",
        videoSrc: "assets/videos/centrifuge_mini_close_lid.mp4",
        cardSummary:
          "A lid-closing scenario where the closure event, hinge path, and final seated state all matter.",
        prompt:
          "The clip shows a simulated close-lid routine on the mini centrifuge. Which transfer signals should stay consistent when the same action family is evaluated on a real instrument?",
        checks: [
          "The lid must travel along the correct hinge path rather than intersecting the housing.",
          "The final closed state should correspond to a physically seated lid, not a near-miss pose.",
          "The policy should preserve clearance between gripper and lid edge during release.",
          "The episode should only pass once the rotor area is actually enclosed and ready for spin.",
        ],
        answer:
          "The real-world pass condition has to be state-based: seated lid, clear release, and enclosed rotor. Matching the simulated trajectory shape is weaker than matching the actual instrument state change.",
      },
    ],
  },
];

class InstrumentViewer {
  constructor(container) {
    this.container = container;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.container.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color("#101010");

    this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    this.camera.position.set(0, 1.4, 4.8);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 0.8;
    this.controls.minDistance = 1.5;
    this.controls.maxDistance = 10;

    this.root = new THREE.Group();
    this.scene.add(this.root);

    this.scene.add(new THREE.HemisphereLight(0xf4fff3, 0x0d0d0d, 1.2));
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(4, 6, 5);
    this.scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0x96ffe7, 0.55);
    fillLight.position.set(-3, 2, -4);
    this.scene.add(fillLight);

    const grid = new THREE.GridHelper(12, 24, 0x2c2c2c, 0x1d1d1d);
    grid.position.y = -1.35;
    this.scene.add(grid);

    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(4.5, 64),
      new THREE.MeshBasicMaterial({ color: 0x161616, opacity: 0.85, transparent: true })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -1.34;
    this.scene.add(floor);

    this.objLoader = new OBJLoader();
    this.stlLoader = new STLLoader();
    this.cache = new Map();
    this.clock = new THREE.Clock();
    this.loadVersion = 0;

    this.handleResize = this.handleResize.bind(this);
    window.addEventListener("resize", this.handleResize);
    this.handleResize();
    this.animate();
  }

  animate() {
    this.animationHandle = requestAnimationFrame(() => this.animate());
    this.controls.update(this.clock.getDelta());
    this.renderer.render(this.scene, this.camera);
  }

  handleResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight || 420;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  async loadModel(modelKey) {
    const definition = MODEL_LIBRARY[modelKey];
    if (!definition) return;

    const loadVersion = ++this.loadVersion;
    this.root.clear();
    const model = await this.getModelClone(modelKey, definition);
    if (loadVersion !== this.loadVersion) return;
    this.root.add(model);
    this.fitCameraToRoot();
  }

  async getModelClone(modelKey, definition) {
    if (!this.cache.has(modelKey)) {
      const built = await this.buildModel(definition);
      this.cache.set(modelKey, built);
    }
    return this.cache.get(modelKey).clone(true);
  }

  async buildModel(definition) {
    const group = new THREE.Group();
    const partConfigs = definition.parts || definition.stl || [];

    const parts = await Promise.all(
      partConfigs.map(async ([path, color]) => {
        const ext = path.split(".").pop().toLowerCase();
        if (ext === "obj") {
          return this.loadObjPart(path, color);
        }
        if (ext === "stl") {
          return this.loadStlPart(path, color);
        }
        return null;
      })
    );

    parts.filter(Boolean).forEach((part) => group.add(part));

    const [rx, ry, rz] = definition.rotation || [0, 0, 0];
    group.rotation.set(rx, ry, rz);
    this.normalizeGroup(group, definition.targetSize || 3);
    return group;
  }

  async loadObjPart(path, color) {
    try {
      const object = await this.objLoader.loadAsync(path);
      object.traverse((child) => {
        if (child.isMesh) {
          child.material = new THREE.MeshStandardMaterial({
            color,
            metalness: 0.16,
            roughness: 0.74,
          });
        }
      });
      return object;
    } catch (error) {
      console.warn(`Failed to load OBJ part: ${path}`, error);
      return null;
    }
  }

  async loadStlPart(path, color) {
    try {
      const geometry = await this.stlLoader.loadAsync(path);
      geometry.computeVertexNormals();
      return new THREE.Mesh(
        geometry,
        new THREE.MeshStandardMaterial({
          color,
          metalness: 0.12,
          roughness: 0.65,
        })
      );
    } catch (error) {
      console.warn(`Failed to load STL part: ${path}`, error);
      return null;
    }
  }

  normalizeGroup(group, targetSize) {
    const box = new THREE.Box3().setFromObject(group);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const scale = targetSize / maxDim;
    group.scale.setScalar(scale);

    const scaledBox = new THREE.Box3().setFromObject(group);
    const center = scaledBox.getCenter(new THREE.Vector3());
    group.position.sub(center);

    const groundedBox = new THREE.Box3().setFromObject(group);
    group.position.y -= groundedBox.min.y + 0.25;
  }

  fitCameraToRoot() {
    const box = new THREE.Box3().setFromObject(this.root);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;

    const distance = maxDim * 1.65;
    this.camera.position.set(distance * 0.95, distance * 0.75, distance * 1.15);
    this.controls.target.copy(center);
    this.controls.update();
  }

  resetView() {
    this.fitCameraToRoot();
  }
}

const dom = {
  sectionNav: document.getElementById("section-nav"),
  sectionKicker: document.getElementById("section-kicker"),
  sectionTitle: document.getElementById("section-title"),
  sectionSummary: document.getElementById("section-summary"),
  modelLabel: document.getElementById("model-label"),
  viewerDescription: document.getElementById("viewer-description"),
  viewerTags: document.getElementById("viewer-tags"),
  mediaImage: document.getElementById("media-image"),
  mediaVideo: document.getElementById("media-video"),
  itemList: document.getElementById("item-list"),
  itemKind: document.getElementById("item-kind"),
  itemTitle: document.getElementById("item-title"),
  itemBody: document.getElementById("item-body"),
  resetView: document.getElementById("reset-view"),
  viewer: document.getElementById("viewer"),
};

const viewer = new InstrumentViewer(dom.viewer);

function getSectionById(sectionId) {
  return SECTIONS.find((entry) => entry.id === sectionId) || SECTIONS[0];
}

function getItemById(section, itemId) {
  return section.items.find((entry) => entry.id === itemId) || section.items[0];
}

function getInitialState() {
  const params = new URLSearchParams(window.location.search);
  const requestedSection = params.get("section") || SECTIONS[0].id;
  const section = getSectionById(requestedSection);
  const requestedItem = params.get("item") || section.items[0].id;
  const item = getItemById(section, requestedItem);

  return {
    sectionId: section.id,
    itemId: item.id,
  };
}

const state = getInitialState();

function syncUrl(sectionId, itemId) {
  const params = new URLSearchParams(window.location.search);
  params.set("section", sectionId);
  params.set("item", itemId);
  const nextUrl = `${window.location.pathname}?${params.toString()}`;
  window.history.replaceState({}, "", nextUrl);
}

function renderNav() {
  dom.sectionNav.innerHTML = "";
  SECTIONS.forEach((section) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `nav-button${state.sectionId === section.id ? " active" : ""}`;
    button.innerHTML = `
      <span class="nav-label">${section.label} · ${section.navTitle}</span>
      <span class="nav-meta">${section.navMeta}</span>
    `;
    button.addEventListener("click", () => {
      state.sectionId = section.id;
      state.itemId = section.items[0].id;
      render();
    });
    dom.sectionNav.appendChild(button);
  });
}

function renderItemList(section) {
  dom.itemList.innerHTML = "";
  section.items.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `item-button${state.itemId === item.id ? " active" : ""}`;
    button.innerHTML = `
      <span class="item-title">${item.title}</span>
      <span class="item-summary">${item.cardSummary}</span>
    `;
    button.addEventListener("click", () => {
      state.itemId = item.id;
      render();
    });
    dom.itemList.appendChild(button);
  });
}

function renderViewer(item) {
  const model = MODEL_LIBRARY[item.modelKey];
  dom.modelLabel.textContent = model.label;
  dom.viewerDescription.textContent = model.description;
  dom.viewerTags.innerHTML = "";
  model.tags.forEach((tag) => {
    const span = document.createElement("span");
    span.className = "viewer-tag";
    span.textContent = tag;
    dom.viewerTags.appendChild(span);
  });

  dom.mediaImage.src = item.imageSrc;
  dom.mediaImage.alt = `${item.title} thumbnail`;

  const mediaPanel = dom.mediaImage.parentElement;
  if (item.videoSrc) {
    mediaPanel.classList.remove("single-media");
    dom.mediaVideo.hidden = false;
    dom.mediaVideo.src = item.videoSrc;
  } else {
    mediaPanel.classList.add("single-media");
    dom.mediaVideo.hidden = true;
    dom.mediaVideo.removeAttribute("src");
    dom.mediaVideo.load();
  }

  viewer.loadModel(item.modelKey);
}

function createTextBlock(title, content) {
  const block = document.createElement("section");
  block.className = "detail-block";
  const heading = document.createElement("h4");
  heading.textContent = title;
  const paragraph = document.createElement("p");
  paragraph.textContent = content;
  block.append(heading, paragraph);
  return block;
}

function createListBlock(title, items, ordered = false) {
  const block = document.createElement("section");
  block.className = "detail-block";
  const heading = document.createElement("h4");
  heading.textContent = title;
  const list = document.createElement(ordered ? "ol" : "ul");
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });
  block.append(heading, list);
  return block;
}

function createOptionBlock(options) {
  const block = document.createElement("section");
  block.className = "detail-block";
  const heading = document.createElement("h4");
  heading.textContent = "Question";
  const list = document.createElement("div");
  list.className = "option-list";
  options.forEach(([key, text]) => {
    const item = document.createElement("div");
    item.className = "option-item";
    item.innerHTML = `<span class="option-key">${key}</span><span>${text}</span>`;
    list.appendChild(item);
  });
  block.append(heading, list);
  return block;
}

function createCodeBlock(title, code) {
  const block = document.createElement("section");
  block.className = "detail-block";
  const heading = document.createElement("h4");
  heading.textContent = title;
  const pre = document.createElement("pre");
  pre.className = "code-block";
  pre.textContent = code;
  block.append(heading, pre);
  return block;
}

function createAnswerBox(title, text, className) {
  const block = document.createElement("section");
  block.className = "detail-block";
  const heading = document.createElement("h4");
  heading.textContent = title;
  const box = document.createElement("div");
  box.className = className;
  box.textContent = text;
  block.append(heading, box);
  return block;
}

function renderItemBody(section, item) {
  dom.itemKind.textContent = item.kind;
  dom.itemTitle.textContent = item.title;
  dom.itemBody.innerHTML = "";

  dom.itemBody.appendChild(createTextBlock("Prompt", item.prompt));

  if (section.id === "part-1") {
    dom.itemBody.appendChild(createOptionBlock(item.options));
    dom.itemBody.appendChild(createAnswerBox("Reference Answer", item.answer, "answer-box"));
    dom.itemBody.appendChild(createListBlock("Alignment Notes", item.notes));
    return;
  }

  if (section.id === "part-2") {
    dom.itemBody.appendChild(createCodeBlock("Action Pool", item.actionPool.join("\n")));
    dom.itemBody.appendChild(createCodeBlock("Reference Python Program", item.referenceProgram));
    dom.itemBody.appendChild(createListBlock("AST-Centric Scoring Signals", item.scoring));
    return;
  }

  dom.itemBody.appendChild(createListBlock("Transfer Checks", item.checks));
  dom.itemBody.appendChild(createAnswerBox("Reference Interpretation", item.answer, "score-box"));
}

function render() {
  const section = getSectionById(state.sectionId);
  const item = getItemById(section, state.itemId);
  state.sectionId = section.id;
  state.itemId = item.id;

  renderNav();
  renderItemList(section);

  dom.sectionKicker.textContent = section.kicker;
  dom.sectionTitle.textContent = section.title;
  dom.sectionSummary.textContent = section.summary;

  renderViewer(item);
  renderItemBody(section, item);
  syncUrl(section.id, item.id);
}

dom.resetView.addEventListener("click", () => viewer.resetView());

render();
