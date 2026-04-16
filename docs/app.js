import * as THREE from "three";
import { OrbitControls } from "https://unpkg.com/three@0.168.0/examples/jsm/controls/OrbitControls.js";
import { OBJLoader } from "https://unpkg.com/three@0.168.0/examples/jsm/loaders/OBJLoader.js";
import { STLLoader } from "https://unpkg.com/three@0.168.0/examples/jsm/loaders/STLLoader.js";

const SITE_BASE = new URL(".", window.location.href);

function assetUrl(path) {
  return new URL(path, SITE_BASE).toString();
}

const MODEL_LIBRARY = {
  thermalCycler: {
    label: "Thermal cycler / Bio-Rad C1000",
    description:
      "Composite OBJ assembly copied from AutoBio visual meshes. This is the anchor asset for PCR-centric benchmark items.",
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
    tags: ["AutoBio asset", "OBJ assembly", "PCR instrument"],
  },
  centrifugeMini: {
    label: "Mini centrifuge / Tiangen Tgear",
    description:
      "Composite OBJ assembly with a visible lid and rotor region. It is useful for asset understanding and transfer tasks.",
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
    tags: ["AutoBio asset", "OBJ assembly", "Rotor task"],
  },
  thermalMixer: {
    label: "Thermal mixer / Eppendorf C",
    description:
      "Composite OBJ assembly with a control-panel region that fits protocol planning around heating and shaking actions.",
    parts: [
      ["assets/models/thermal_mixer/body-visual-0.obj", "#c8c2ad"],
      ["assets/models/thermal_mixer/body-visual-1.obj", "#2f2f2f"],
      ["assets/models/thermal_mixer/body-visual-2.obj", "#c8c2ad"],
      ["assets/models/thermal_mixer/body-visual-3.obj", "#395e94"],
      ["assets/models/thermal_mixer/body-visual-4.obj", "#969184"],
    ],
    rotation: [-Math.PI / 2, 0, Math.PI],
    targetSize: 3.1,
    tags: ["AutoBio asset", "OBJ assembly", "Heating and mixing"],
  },
  tube15ml: {
    label: "15 mL centrifuge tube",
    description:
      "Two-piece STL assembly of a 15 mL screw-cap tube. It is used as a light-weight transfer object in embodied settings.",
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
    label: "Level 1",
    navTitle: "Asset Understanding",
    navMeta: "Single 3D asset + multiple-choice question",
    kicker: "Level 1",
    title: "Asset Understanding",
    summary:
      "Level 1 presents a single lab asset in 3D and asks a multiple-choice question about how that asset is used.",
    note:
      "Level 1 keeps the left-side view focused on one interactive 3D asset so the question is grounded in a single instrument.",
    samples: [
      {
        id: "asset-q1",
        tabTitle: "Question 1",
        tabMeta: "Thermal cycler",
        kind: "Asset question",
        title: "Thermal cycler lid-state question",
        modelKey: "thermalCycler",
        prompt:
          "Rotate the thermal cycler in the 3D viewer and answer the following question. Which state change must happen before a PCR run can start safely?",
        options: [
          ["A", "Leave the lid open and only set the denaturation temperature."],
          ["B", "Close and secure the lid so the heated top presses the reaction plate."],
          ["C", "Remove the plate after power-on and keep the block empty."],
          ["D", "Disable cooling and keep the lid lever floating above the block."],
        ],
        answer:
          "Correct answer: B. The reaction vessel has to be seated and the lid has to be secured before thermocycling begins.",
        notes: [
          "Nature Protocols grounding: PCR workflows depend on stable heated-lid pressure to control condensation.",
          "Embodied alignment: the same lid operation is exposed in AutoBio-style thermal cycler interaction tasks.",
        ],
      },
      {
        id: "asset-q2",
        tabTitle: "Question 2",
        tabMeta: "Mini centrifuge",
        kind: "Asset question",
        title: "Mini centrifuge rotor-region question",
        modelKey: "centrifugeMini",
        prompt:
          "Inspect the mini centrifuge in the 3D viewer. The central black circular structure is visible inside the housing. What is its function in the workflow?",
        options: [
          ["A", "It is the rotor seat that holds balanced tubes during spinning."],
          ["B", "It is a heating block used for PCR amplification."],
          ["C", "It is a waste reservoir for discarded supernatant."],
          ["D", "It is an imaging sensor for barcode reading."],
        ],
        answer:
          "Correct answer: A. The central structure is the rotor region, which matters for loading, balancing, spinning, and lid closure.",
        notes: [
          "Scientific grounding: centrifugation steps require correct tube placement and balancing.",
          "Embodied alignment: rotor loading and lid closing are both reusable action families in embodied benchmarks.",
        ],
      },
    ],
  },
  {
    id: "part-2",
    label: "Level 2",
    navTitle: "Protocol Question",
    navMeta: "Multiple instruments + long-horizon planning",
    kicker: "Level 2",
    title: "Protocol Question",
    summary:
      "Level 2 shows multiple instruments in the left-side view because the protocol question depends on cross-instrument coordination.",
    note:
      "The left-side view switches to a multi-instrument layout in Level 2 so the protocol question is tied to a broader instrument set rather than a single asset.",
    samples: [
      {
        id: "plan-q1",
        tabTitle: "Question 1",
        tabMeta: "qPCR protocol",
        kind: "Protocol question",
        title: "qPCR protocol question under a finite action space",
        modelKeys: ["thermalCycler", "centrifugeMini", "tube15ml"],
        displayTitle: "Protocol instrument set",
        displayDescription:
          "This level shows multiple instruments because a concrete protocol question has to coordinate assets, containers, and device transitions across the workflow.",
        displayTags: ["Multi-instrument view", "Protocol planning", "Finite action space"],
        context: [
          "Goal: quantify cytokine-response expression after stimulation with a fixed qPCR panel.",
          "Input to the model: experiment background, reagent list, equipment list, and a finite action space.",
          "Expected output: a Python protocol program composed only from the allowed actions.",
        ],
        prompt:
          "Write a long-horizon protocol that prepares the plate, loads the thermal cycler, secures the lid, configures the program, runs it, and unloads the plate.",
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
        outputRequirements: [
          "Use only functions from the finite action space.",
          "Return a valid Python program that can be parsed with the Python AST.",
          "Specify concrete arguments for instrument, plate, seal type, and runtime.",
          "Keep the step order consistent with the physical protocol.",
        ],
        referenceProgram: `qpcr_plate = aliquot_master_mix(\n    reagent_set="cytokine_qpcr_mix",\n    destination_plate="96_well_plate",\n    volume_ul=18,\n)\n\nloaded_plate = load_samples(\n    sample_tubes="stimulated_rna_samples",\n    destination_plate=qpcr_plate,\n    layout="triplicate_layout",\n)\n\nsealed_plate = seal_plate(\n    plate=loaded_plate,\n    seal_type="optical_film",\n)\n\ncycler_slot = place_plate_in_thermal_cycler(\n    plate=sealed_plate,\n    instrument="thermal_cycler_biorad_c1000",\n)\n\nlid_state = close_thermal_cycler_lid(\n    instrument="thermal_cycler_biorad_c1000",\n    pressure_mode="heated_lid_secure",\n)\n\nprogram_state = set_pcr_program(\n    instrument="thermal_cycler_biorad_c1000",\n    protocol_name="cytokine_panel_qpcr",\n)\n\nrun_state = run_pcr_program(\n    instrument="thermal_cycler_biorad_c1000",\n    runtime_min=95,\n)\n\ncompleted_plate = unload_plate(\n    instrument="thermal_cycler_biorad_c1000",\n    plate=sealed_plate,\n)`,
        evaluation: [
          "AST parse success for the generated Python program.",
          "Allowed-call accuracy against the finite action space.",
          "Argument-match accuracy for plate, instrument, seal type, and runtime.",
          "Dependency ordering from plate preparation to execution.",
        ],
      },
      {
        id: "plan-q2",
        tabTitle: "Question 2",
        tabMeta: "Thermal mixer protocol",
        kind: "Protocol question",
        title: "Thermal mixer incubation protocol question",
        modelKeys: ["thermalMixer", "centrifugeMini", "tube15ml"],
        displayTitle: "Protocol instrument set",
        displayDescription:
          "The visible instrument set is broader than a single mixer because long-horizon planning has to reason across preparation, incubation, and post-incubation handling.",
        displayTags: ["Multi-instrument view", "Protocol planning", "Cross-asset context"],
        context: [
          "Goal: execute a protein-binding incubation with heating, interval mixing, and post-incubation aliquoting.",
          "Input to the model: assay description plus a finite action space.",
          "Expected output: a Python protocol program that remains inside the allowed action space.",
        ],
        prompt:
          "Write a long-horizon protocol that loads tubes, locks the block, sets temperature and shaking parameters, runs the incubation, performs a brief spin, and collects the final aliquot.",
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
        outputRequirements: [
          "Use only functions from the finite action space.",
          "Return a valid Python program with explicit parameter settings.",
          "Match the order required by the physical protocol.",
          "Preserve the relation between the mixer asset and the chosen control actions.",
        ],
        referenceProgram: `loaded_tubes = load_tubes_into_mixer(\n    tube_set="binding_reaction_triplicates",\n    rack_slot="thermomixer_block_a",\n    instrument="thermal_mixer_eppendorf_c",\n)\n\nblock_state = lock_mixer_block(\n    instrument="thermal_mixer_eppendorf_c",\n    block_type="1.5mL_tube_block",\n)\n\ntemp_state = set_mixer_temperature(\n    instrument="thermal_mixer_eppendorf_c",\n    target_celsius=37,\n)\n\nspeed_state = set_mixer_speed(\n    instrument="thermal_mixer_eppendorf_c",\n    rpm=900,\n    mode="interval_mix",\n)\n\nduration_state = set_mixer_duration(\n    instrument="thermal_mixer_eppendorf_c",\n    duration_min=45,\n)\n\nrun_state = start_mixer_run(\n    instrument="thermal_mixer_eppendorf_c",\n)\n\nspin_state = pause_and_brief_spin(\n    tube_set=loaded_tubes,\n    spin_seconds=8,\n)\n\naliquot_state = collect_post_incubation_aliquot(\n    tube_set=loaded_tubes,\n    volume_ul=25,\n    destination="assay_plate_b",\n)`,
        evaluation: [
          "Allowed-call accuracy against the finite action space.",
          "Argument-match accuracy for temperature, speed, duration, and aliquot volume.",
          "Protocol length adequacy rather than short-form summarization.",
          "Action consistency between the thermal mixer asset and the output program.",
        ],
      },
    ],
  },
  {
    id: "part-3",
    label: "Level 3",
    navTitle: "Video Preview",
    navMeta: "Video + transfer-oriented question",
    kicker: "Level 3",
    title: "Sim2Real Video",
    summary:
      "Level 3 replaces the 3D asset on the left side with a video so the question can focus on transfer-oriented observations.",
    note:
      "The left-side view switches to video in Level 3 because the benchmark is emphasizing observable execution and transfer conditions rather than static asset structure.",
    samples: [
      {
        id: "sim-q1",
        tabTitle: "Question 1",
        tabMeta: "Tube pickup",
        kind: "Transfer preview",
        title: "Tube pickup transfer check",
        videoTitle: "Tube pickup episode",
        videoDescription:
          "The left-side view is a video in Level 3. This clip is used to anchor the transfer-oriented question to an observable execution trace.",
        videoTags: ["Embodied clip", "Transfer preview", "Tube handling"],
        prompt:
          "Observe the tube-pickup video and answer the following question. Which signals should matter before a simulated pickup is considered transferable to the real bench?",
        checks: [
          "The gripper contacts the tube body instead of clipping through the cap.",
          "The tube remains stable after lift-off instead of slipping or oscillating.",
          "The post-grasp orientation remains usable for the next protocol step.",
          "Success depends on the object state, not only the arm trajectory.",
        ],
        answer:
          "A useful sim2real transfer signal must score grasp stability, pose consistency, and downstream usability rather than only matching the nominal motion.",
        videoSrc: "assets/videos/pickup_tube.mp4",
      },
      {
        id: "sim-q2",
        tabTitle: "Question 2",
        tabMeta: "Centrifuge lid",
        kind: "Transfer preview",
        title: "Mini centrifuge lid-closure transfer check",
        videoTitle: "Centrifuge lid-closure episode",
        videoDescription:
          "This clip keeps the left-side view tied to a concrete execution trace, so the question can focus on closure state, release, and transfer readiness.",
        videoTags: ["Embodied clip", "Transfer preview", "Closure event"],
        prompt:
          "Observe the centrifuge lid-closure video and answer the following question. Which conditions should stay consistent when the same close-lid routine is evaluated on the real instrument?",
        checks: [
          "The lid follows a valid hinge path instead of intersecting the housing.",
          "The final state corresponds to a seated, closed lid rather than a near-miss pose.",
          "The release keeps clearance between the gripper and the lid edge.",
          "The pass condition requires the rotor region to be enclosed and ready for spin.",
        ],
        answer:
          "The real-world pass condition should be state-based: seated lid, clear release, enclosed rotor, and readiness for the next physical step.",
        videoSrc: "assets/videos/centrifuge_mini_close_lid.mp4",
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
    this.scene.background = new THREE.Color("#101111");

    this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    this.camera.position.set(0, 1.3, 4.6);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 0.8;
    this.controls.minDistance = 1.5;
    this.controls.maxDistance = 10;

    this.root = new THREE.Group();
    this.scene.add(this.root);

    this.scene.add(new THREE.HemisphereLight(0xf5fff3, 0x0d0e0e, 1.2));
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.35);
    keyLight.position.set(4, 6, 5);
    this.scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0x96ffe7, 0.5);
    fillLight.position.set(-3, 2, -4);
    this.scene.add(fillLight);

    const grid = new THREE.GridHelper(12, 24, 0x2c2c2c, 0x1d1d1d);
    grid.position.y = -1.35;
    this.scene.add(grid);

    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(4.5, 64),
      new THREE.MeshBasicMaterial({ color: 0x161818, opacity: 0.85, transparent: true })
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
    const height = this.container.clientHeight || 460;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  async loadModel(modelKey) {
    const definition = MODEL_LIBRARY[modelKey];
    if (!definition) {
      throw new Error(`Unknown model key: ${modelKey}`);
    }

    const loadVersion = ++this.loadVersion;
    const model = await this.getModelClone(modelKey, definition);
    if (loadVersion !== this.loadVersion) {
      return false;
    }

    this.root.clear();
    this.root.add(model);
    this.fitCameraToRoot();
    return this.root.children.length > 0;
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
        const extension = path.split(".").pop().toLowerCase();
        const resolvedPath = assetUrl(path);

        if (extension === "obj") {
          return this.loadObjPart(resolvedPath, color);
        }

        if (extension === "stl") {
          return this.loadStlPart(resolvedPath, color);
        }

        return null;
      })
    );

    parts.filter(Boolean).forEach((part) => group.add(part));

    if (!group.children.length) {
      throw new Error(`No geometry loaded for ${definition.label}`);
    }

    const [rx, ry, rz] = definition.rotation || [0, 0, 0];
    group.rotation.set(rx, ry, rz);
    this.normalizeGroup(group, definition.targetSize || 3);
    return group;
  }

  async loadObjPart(path, color) {
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
  }

  async loadStlPart(path, color) {
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
  sampleTabs: document.getElementById("sample-tabs"),
  featureKicker: document.getElementById("feature-kicker"),
  featureTitle: document.getElementById("feature-title"),
  featureDescription: document.getElementById("feature-description"),
  featureTags: document.getElementById("feature-tags"),
  singleViewStage: document.getElementById("single-view-stage"),
  multiViewStage: document.getElementById("multi-view-stage"),
  videoStage: document.getElementById("video-stage"),
  viewerStatus: document.getElementById("viewer-status"),
  featureVideo: document.getElementById("feature-video"),
  miniCards: Array.from(document.querySelectorAll(".mini-view-card")),
  miniTitles: [0, 1, 2].map((index) => document.getElementById(`mini-title-${index}`)),
  miniStatuses: [0, 1, 2].map((index) => document.getElementById(`mini-status-${index}`)),
  resetView: document.getElementById("reset-view"),
  viewer: document.getElementById("viewer"),
  itemKind: document.getElementById("item-kind"),
  itemTitle: document.getElementById("item-title"),
  itemBody: document.getElementById("item-body"),
  levelNoteBody: document.getElementById("level-note-body"),
};

const mainViewer = new InstrumentViewer(dom.viewer);
const miniViewers = [0, 1, 2].map((index) => new InstrumentViewer(document.getElementById(`mini-viewer-${index}`)));

function getSectionById(sectionId) {
  return SECTIONS.find((entry) => entry.id === sectionId) || SECTIONS[0];
}

function getSampleById(section, sampleId) {
  return section.samples.find((entry) => entry.id === sampleId) || section.samples[0];
}

function getInitialState() {
  const params = new URLSearchParams(window.location.search);
  const requestedSection = params.get("section") || SECTIONS[0].id;
  const section = getSectionById(requestedSection);
  const requestedSample = params.get("item") || params.get("sample") || section.samples[0].id;
  const sample = getSampleById(section, requestedSample);

  return {
    sectionId: section.id,
    sampleId: sample.id,
  };
}

const state = getInitialState();

function syncUrl(sectionId, sampleId) {
  const params = new URLSearchParams(window.location.search);
  params.set("section", sectionId);
  params.set("item", sampleId);
  window.history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
}

function setStatus(node, text, visible) {
  node.textContent = text;
  node.classList.toggle("is-hidden", !visible);
}

function renderTags(tags) {
  dom.featureTags.innerHTML = "";
  tags.forEach((tag) => {
    const chip = document.createElement("span");
    chip.className = "feature-tag";
    chip.textContent = tag;
    dom.featureTags.appendChild(chip);
  });
}

function showFeatureMode(mode) {
  dom.singleViewStage.hidden = mode !== "single";
  dom.multiViewStage.hidden = mode !== "multi";
  dom.videoStage.hidden = mode !== "video";
}

function resetVideoStage() {
  dom.featureVideo.pause();
  dom.featureVideo.removeAttribute("src");
  dom.featureVideo.load();
}

async function renderSingleAsset(sample) {
  const model = MODEL_LIBRARY[sample.modelKey];

  dom.featureKicker.textContent = "3D Asset";
  dom.featureTitle.textContent = model.label;
  dom.featureDescription.textContent = model.description;
  renderTags(model.tags);
  dom.resetView.hidden = false;

  resetVideoStage();
  showFeatureMode("single");
  mainViewer.handleResize();
  setStatus(dom.viewerStatus, "Loading 3D asset...", true);

  try {
    const loaded = await mainViewer.loadModel(sample.modelKey);
    if (!loaded) {
      throw new Error("No model content was added to the scene.");
    }
    setStatus(dom.viewerStatus, "", false);
  } catch (error) {
    console.error(error);
    setStatus(
      dom.viewerStatus,
      "The 3D asset could not be rendered in this browser session. The model files are present, but the viewer failed to load them.",
      true
    );
  }
}

async function renderInstrumentSet(sample) {
  const modelKeys = sample.modelKeys || [];

  dom.featureKicker.textContent = "Instrument Set";
  dom.featureTitle.textContent = sample.displayTitle;
  dom.featureDescription.textContent = sample.displayDescription;
  renderTags(sample.displayTags || []);
  dom.resetView.hidden = true;

  resetVideoStage();
  showFeatureMode("multi");
  setStatus(dom.viewerStatus, "", false);

  await Promise.all(
    dom.miniCards.map(async (card, index) => {
      const modelKey = modelKeys[index];
      if (!modelKey) {
        card.hidden = true;
        return;
      }

      card.hidden = false;
      const model = MODEL_LIBRARY[modelKey];
      dom.miniTitles[index].textContent = model.label;
      miniViewers[index].handleResize();
      setStatus(dom.miniStatuses[index], "Loading 3D asset...", true);

      try {
        const loaded = await miniViewers[index].loadModel(modelKey);
        if (!loaded) {
          throw new Error("No model content was added to the scene.");
        }
        setStatus(dom.miniStatuses[index], "", false);
      } catch (error) {
        console.error(error);
        setStatus(dom.miniStatuses[index], "The 3D asset failed to load.", true);
      }
    })
  );
}

function renderVideo(sample) {
  dom.featureKicker.textContent = "Video";
  dom.featureTitle.textContent = sample.videoTitle;
  dom.featureDescription.textContent = sample.videoDescription;
  renderTags(sample.videoTags || []);
  dom.resetView.hidden = true;

  showFeatureMode("video");
  setStatus(dom.viewerStatus, "", false);

  dom.featureVideo.src = assetUrl(sample.videoSrc);
  dom.featureVideo.load();
}

async function renderFeature(section, sample) {
  if (section.id === "part-1") {
    await renderSingleAsset(sample);
    return;
  }

  if (section.id === "part-2") {
    await renderInstrumentSet(sample);
    return;
  }

  renderVideo(sample);
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
  heading.textContent = "Options";

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
      state.sampleId = section.samples[0].id;
      render();
    });
    dom.sectionNav.appendChild(button);
  });
}

function renderSampleTabs(section) {
  dom.sampleTabs.innerHTML = "";

  section.samples.forEach((sample) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `sample-button${state.sampleId === sample.id ? " active" : ""}`;
    button.innerHTML = `
      <span class="sample-title">${sample.tabTitle}</span>
      <span class="sample-meta">${sample.tabMeta}</span>
    `;
    button.addEventListener("click", () => {
      state.sampleId = sample.id;
      render();
    });
    dom.sampleTabs.appendChild(button);
  });
}

function renderItemBody(section, sample) {
  dom.itemKind.textContent = sample.kind;
  dom.itemTitle.textContent = sample.title;
  dom.itemBody.innerHTML = "";

  if (section.id === "part-1") {
    dom.itemBody.appendChild(createTextBlock("Question", sample.prompt));
    dom.itemBody.appendChild(createOptionBlock(sample.options));
    dom.itemBody.appendChild(createAnswerBox("Reference answer", sample.answer, "answer-box"));
    dom.itemBody.appendChild(createListBlock("Why this matters", sample.notes));
    return;
  }

  if (section.id === "part-2") {
    const visibleInstruments = sample.modelKeys.map((modelKey) => MODEL_LIBRARY[modelKey].label);
    dom.itemBody.appendChild(createListBlock("Visible instruments", visibleInstruments));
    dom.itemBody.appendChild(createListBlock("Background", sample.context));
    dom.itemBody.appendChild(createTextBlock("Question", sample.prompt));
    dom.itemBody.appendChild(createCodeBlock("Finite action space", sample.actionPool.join("\n")));
    dom.itemBody.appendChild(createListBlock("Output requirements", sample.outputRequirements));
    dom.itemBody.appendChild(createCodeBlock("Reference Python program", sample.referenceProgram));
    dom.itemBody.appendChild(createListBlock("Evaluation focus", sample.evaluation));
    return;
  }

  dom.itemBody.appendChild(createTextBlock("Question", sample.prompt));
  dom.itemBody.appendChild(createListBlock("Transfer checks", sample.checks));
  dom.itemBody.appendChild(createAnswerBox("Reference interpretation", sample.answer, "score-box"));
}

async function render() {
  const section = getSectionById(state.sectionId);
  const sample = getSampleById(section, state.sampleId);

  state.sectionId = section.id;
  state.sampleId = sample.id;

  renderNav();
  renderSampleTabs(section);

  dom.sectionKicker.textContent = section.kicker;
  dom.sectionTitle.textContent = section.title;
  dom.sectionSummary.textContent = section.summary;
  dom.levelNoteBody.innerHTML = `<p>${section.note}</p>`;

  renderItemBody(section, sample);
  await renderFeature(section, sample);
  syncUrl(section.id, sample.id);
}

dom.resetView.addEventListener("click", () => mainViewer.resetView());

render();
