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
    navTitle: "Long-Horizon Planing",
    navMeta: "Multiple instruments + long-horizon planing",
    kicker: "Level 2",
    title: "Long-Horizon Planing",
    summary:
      "Level 2 shows multiple instruments in the left-side view because the protocol question depends on cross-instrument coordination.",
    note:
      "The left-side view switches to a multi-instrument layout in Level 2 so the protocol question is tied to a broader instrument set rather than a single asset.",
    samples: [
      {
        id: "plan-q1",
        tabTitle: "Question 1",
        tabMeta: "qPCR protocol",
        kind: "Long-Horizon Planing",
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
        outputRequirements: [
          "Use only functions from the finite action space.",
          "Return a valid Python program that can be parsed with the Python AST.",
          "Specify concrete arguments for instrument, plate, seal type, and runtime.",
          "Keep the step order consistent with the physical protocol.",
        ],
        referenceSteps: [
          {
            title: "Aliquot master mix",
            code: 'qpcr_plate = aliquot_master_mix(reagent_set="cytokine_qpcr_mix", destination_plate="96_well_plate", volume_ul=18)',
          },
          {
            title: "Load samples",
            code: 'loaded_plate = load_samples(sample_tubes="stimulated_rna_samples", destination_plate=qpcr_plate, layout="triplicate_layout")',
          },
          {
            title: "Seal plate",
            code: 'sealed_plate = seal_plate(plate=loaded_plate, seal_type="optical_film")',
          },
          {
            title: "Load thermal cycler",
            code: 'cycler_slot = place_plate_in_thermal_cycler(plate=sealed_plate, instrument="thermal_cycler_biorad_c1000")',
          },
          {
            title: "Secure lid",
            code: 'lid_state = close_thermal_cycler_lid(instrument="thermal_cycler_biorad_c1000", pressure_mode="heated_lid_secure")',
          },
          {
            title: "Set PCR program",
            code: 'program_state = set_pcr_program(instrument="thermal_cycler_biorad_c1000", protocol_name="cytokine_panel_qpcr")',
          },
          {
            title: "Run PCR program",
            code: 'run_state = run_pcr_program(instrument="thermal_cycler_biorad_c1000", runtime_min=95)',
          },
          {
            title: "Unload plate",
            code: 'completed_plate = unload_plate(instrument="thermal_cycler_biorad_c1000", plate=sealed_plate)',
          },
        ],
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
        kind: "Long-Horizon Planing",
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
        outputRequirements: [
          "Use only functions from the finite action space.",
          "Return a valid Python program with explicit parameter settings.",
          "Match the order required by the physical protocol.",
          "Preserve the relation between the mixer asset and the chosen control actions.",
        ],
        referenceSteps: [
          {
            title: "Load tubes into mixer",
            code: 'loaded_tubes = load_tubes_into_mixer(tube_set="binding_reaction_triplicates", rack_slot="thermomixer_block_a", instrument="thermal_mixer_eppendorf_c")',
          },
          {
            title: "Lock mixer block",
            code: 'block_state = lock_mixer_block(instrument="thermal_mixer_eppendorf_c", block_type="1.5mL_tube_block")',
          },
          {
            title: "Set temperature",
            code: 'temp_state = set_mixer_temperature(instrument="thermal_mixer_eppendorf_c", target_celsius=37)',
          },
          {
            title: "Set shaking speed",
            code: 'speed_state = set_mixer_speed(instrument="thermal_mixer_eppendorf_c", rpm=900, mode="interval_mix")',
          },
          {
            title: "Set duration",
            code: 'duration_state = set_mixer_duration(instrument="thermal_mixer_eppendorf_c", duration_min=45)',
          },
          {
            title: "Start mixer run",
            code: 'run_state = start_mixer_run(instrument="thermal_mixer_eppendorf_c")',
          },
          {
            title: "Brief spin",
            code: 'spin_state = pause_and_brief_spin(tube_set=loaded_tubes, spin_seconds=8)',
          },
          {
            title: "Collect final aliquot",
            code: 'aliquot_state = collect_post_incubation_aliquot(tube_set=loaded_tubes, volume_ul=25, destination="assay_plate_b")',
          },
        ],
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
    navTitle: "Sim2Real",
    navMeta: "Multi-view videos + transfer-oriented question",
    kicker: "Level 3",
    title: "Sim2Real",
    summary:
      "Level 3 replaces the 3D asset on the left side with looped multi-view videos so the question can focus on transfer-oriented observations.",
    note:
      "The left-side view switches to looped multi-view videos in Level 3 because the benchmark is emphasizing observable execution and transfer conditions rather than static asset structure.",
    samples: [
      {
        id: "sim-q1",
        tabTitle: "Question 1",
        tabMeta: "Thermal cycler close",
        kind: "Sim2Real",
        title: "Thermal cycler close transfer check",
        videoTitle: "Thermal cycler close videos",
        videoDescription:
          "Level 3 uses paired front-view and wrist-view videos so the transfer-oriented question is grounded in a concrete multi-view execution trace.",
        videoTags: ["Embodied clip", "Sim2Real", "Thermal cycler close"],
        videoSources: [
          { title: "Front view", src: "assets/videos/thermal_cycler_close_front.mp4" },
          { title: "Wrist view", src: "assets/videos/thermal_cycler_close_wrist.mp4" },
        ],
        prompt:
          "Observe the thermal cycler close videos and answer the following question. Which signals should matter before the simulated close-lid routine is considered transferable to the real bench?",
        checks: [
          "The lid follows a valid hinge path instead of intersecting the instrument housing.",
          "The final state is a seated, closed lid rather than a visually near-miss pose.",
          "The end effector releases with enough clearance to avoid bumping the lid edge.",
          "Success is judged by the resulting instrument state, not only by motion similarity.",
        ],
        answer:
          "A useful Sim2Real signal here is state-based: valid hinge motion, seated closure, clean release, and readiness for the next PCR step.",
      },
      {
        id: "sim-q2",
        tabTitle: "Question 2",
        tabMeta: "Insert task",
        kind: "Sim2Real",
        title: "Insert-task transfer check",
        videoTitle: "Insert-task videos",
        videoDescription:
          "These paired videos keep the left-side view tied to a concrete insertion trace so the question can focus on alignment, seating depth, and transfer readiness.",
        videoTags: ["Embodied clip", "Sim2Real", "Insertion"],
        videoSources: [
          { title: "Front view", src: "assets/videos/insert_front.mp4" },
          { title: "Wrist view", src: "assets/videos/insert_wrist.mp4" },
        ],
        prompt:
          "Observe the insert-task videos and answer the following question. Which conditions should stay consistent when the same insertion routine is evaluated on the real bench?",
        checks: [
          "The approach pose stays aligned with the target opening instead of relying on clipping.",
          "Contact leads to a seated insertion state with usable depth, not a partial near-miss.",
          "The object remains stable after release instead of drifting or bouncing out.",
          "Success is judged by insertion state and downstream usability, not only by the arm path.",
        ],
        answer:
          "The real-world pass condition should stay state-based: alignment, seated depth, stable release, and readiness for the next embodied step.",
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
  videoGrid: document.getElementById("video-grid"),
  viewerStatus: document.getElementById("viewer-status"),
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
  dom.videoGrid.querySelectorAll("video").forEach((video) => {
    video.pause();
    video.removeAttribute("src");
    video.load();
  });
  dom.videoGrid.innerHTML = "";
}

function createVideoCard(source, index) {
  const card = document.createElement("article");
  card.className = "video-card";

  const meta = document.createElement("div");
  meta.className = "video-card-meta";

  const kicker = document.createElement("p");
  kicker.className = "video-card-kicker";
  kicker.textContent = `View ${index + 1}`;

  const title = document.createElement("h4");
  title.className = "video-card-title";
  title.textContent = source.title;

  const video = document.createElement("video");
  video.className = "feature-video";
  video.controls = true;
  video.autoplay = true;
  video.muted = true;
  video.loop = true;
  video.playsInline = true;
  video.src = assetUrl(source.src);

  meta.append(kicker, title);
  card.append(meta, video);
  return { card, video };
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
  dom.featureKicker.textContent = "Videos";
  dom.featureTitle.textContent = sample.videoTitle;
  dom.featureDescription.textContent = sample.videoDescription;
  renderTags(sample.videoTags || []);
  dom.resetView.hidden = true;

  resetVideoStage();
  showFeatureMode("video");
  setStatus(dom.viewerStatus, "", false);

  const sources = sample.videoSources || [];
  sources.forEach((source, index) => {
    const { card, video } = createVideoCard(source, index);
    dom.videoGrid.appendChild(card);
    video.load();
    const playPromise = video.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(() => {});
    }
  });
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

function createProtocolStepsBlock(title, steps) {
  const block = document.createElement("section");
  block.className = "detail-block";

  const heading = document.createElement("h4");
  heading.textContent = title;

  const list = document.createElement("div");
  list.className = "protocol-step-list";

  steps.forEach((step, index) => {
    const card = document.createElement("article");
    card.className = "protocol-step-card";

    const meta = document.createElement("div");
    meta.className = "protocol-step-meta";

    const kicker = document.createElement("p");
    kicker.className = "protocol-step-kicker";
    kicker.textContent = `Step ${index + 1}`;

    const titleNode = document.createElement("h5");
    titleNode.className = "protocol-step-title";
    titleNode.textContent = step.title;

    const code = document.createElement("pre");
    code.className = "protocol-step-code";
    code.textContent = step.code;

    meta.append(kicker, titleNode);
    card.append(meta, code);
    list.appendChild(card);
  });

  block.append(heading, list);
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
    dom.itemBody.appendChild(createListBlock("Output requirements", sample.outputRequirements));
    dom.itemBody.appendChild(createProtocolStepsBlock("Reference output steps", sample.referenceSteps));
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
