from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionArgument:
    name: str
    type_hint: str
    description: str


@dataclass(frozen=True)
class ActionSpec:
    name: str
    family: str
    description: str
    returns: str
    return_description: str
    arguments: tuple[ActionArgument, ...]


ACTION_LIBRARY: dict[str, ActionSpec] = {
    "add_reagent": ActionSpec(
        name="add_reagent",
        family="transfer",
        description="Add a named reagent into an existing sample or vessel.",
        returns="str",
        return_description="A handle for the updated sample after reagent addition.",
        arguments=(
            ActionArgument("sample", "str", "Input sample or vessel that receives the reagent."),
            ActionArgument("reagent", "str", "Reagent or buffer being added."),
            ActionArgument("volume_ul", "float", "Added volume in microliters."),
            ActionArgument("mixing", "str", "Mixing instruction applied immediately after addition."),
        ),
    ),
    "aliquot_sample": ActionSpec(
        name="aliquot_sample",
        family="transfer",
        description="Split one sample into a defined aliquot or aliquot series.",
        returns="str",
        return_description="A handle for the aliquoted sample portion.",
        arguments=(
            ActionArgument("sample", "str", "Input sample to split."),
            ActionArgument("destination", "str", "Target tube, plate, or vessel."),
            ActionArgument("volume_ul", "float", "Aliquot volume in microliters."),
            ActionArgument("aliquot_count", "int", "Number of equivalent aliquots prepared in the step."),
        ),
    ),
    "transfer_liquid": ActionSpec(
        name="transfer_liquid",
        family="transfer",
        description="Move liquid from one container to another with a specified tool.",
        returns="str",
        return_description="A handle for the destination sample after transfer.",
        arguments=(
            ActionArgument("source", "str", "Source sample or container."),
            ActionArgument("destination", "str", "Destination sample or container."),
            ActionArgument("volume_ul", "float", "Transferred volume in microliters."),
            ActionArgument("tool", "str", "Pipette or liquid-handling tool used for the transfer."),
        ),
    ),
    "collect_fraction": ActionSpec(
        name="collect_fraction",
        family="transfer",
        description="Collect a named phase or fraction from a processed sample.",
        returns="str",
        return_description="A handle for the collected fraction.",
        arguments=(
            ActionArgument("sample", "str", "Input sample that contains multiple phases or fractions."),
            ActionArgument("phase", "str", "Named phase or fraction to collect."),
            ActionArgument("destination", "str", "Target vessel for the collected fraction."),
            ActionArgument("volume_ul", "float", "Collected volume in microliters."),
        ),
    ),
    "load_plate": ActionSpec(
        name="load_plate",
        family="transfer",
        description="Load one sample into a plate according to a well layout.",
        returns="str",
        return_description="A handle for the updated plate.",
        arguments=(
            ActionArgument("sample", "str", "Input sample or reaction mix to load."),
            ActionArgument("plate", "str", "Destination plate identifier."),
            ActionArgument("well_map", "str", "Well assignment or layout description."),
            ActionArgument("volume_ul", "float", "Loaded volume per destination well."),
        ),
    ),
    "mix_sample": ActionSpec(
        name="mix_sample",
        family="mix",
        description="Mix a sample using a generic laboratory method.",
        returns="str",
        return_description="A handle for the mixed sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample being mixed."),
            ActionArgument("method", "str", "Mixing method such as inversion, pipetting, or rocking."),
            ActionArgument("duration_s", "float", "Mixing duration in seconds."),
            ActionArgument("speed", "str", "Speed setting or qualitative speed description."),
        ),
    ),
    "vortex_mix": ActionSpec(
        name="vortex_mix",
        family="mix",
        description="Mix a sample on a vortex mixer.",
        returns="str",
        return_description="A handle for the vortexed sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample placed on the vortex mixer."),
            ActionArgument("duration_s", "float", "Vortex duration in seconds."),
            ActionArgument("speed_rpm", "int", "Mixer speed in RPM."),
            ActionArgument("temperature_c", "float", "Ambient or controlled temperature during mixing."),
        ),
    ),
    "stir_with_rod": ActionSpec(
        name="stir_with_rod",
        family="mix",
        description="Stir a liquid sample with a glass rod or stirring tool.",
        returns="str",
        return_description="A handle for the stirred sample.",
        arguments=(
            ActionArgument("container", "str", "Container holding the liquid to stir."),
            ActionArgument("duration_s", "float", "Stirring duration in seconds."),
            ActionArgument("speed_desc", "str", "Qualitative stirring intensity."),
            ActionArgument("temperature_c", "float", "Sample temperature during stirring."),
        ),
    ),
    "shake_container": ActionSpec(
        name="shake_container",
        family="mix",
        description="Shake a closed vessel for coarse liquid mixing.",
        returns="str",
        return_description="A handle for the shaken sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample or vessel being shaken."),
            ActionArgument("amplitude_mm", "float", "Shake amplitude in millimeters."),
            ActionArgument("repeat_n", "int", "Number of shake repetitions or cycles."),
            ActionArgument("duration_s", "float", "Total shaking duration in seconds."),
        ),
    ),
    "incubate_sample": ActionSpec(
        name="incubate_sample",
        family="incubate",
        description="Incubate a sample under a defined temperature and condition.",
        returns="str",
        return_description="A handle for the incubated sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample placed into incubation."),
            ActionArgument("temperature_c", "float", "Incubation temperature in Celsius."),
            ActionArgument("duration_min", "float", "Incubation time in minutes."),
            ActionArgument("condition", "str", "Condition such as static, shaking, protected from light, or humidified."),
        ),
    ),
    "heat_sample": ActionSpec(
        name="heat_sample",
        family="incubate",
        description="Heat a sample on a named device or heat source.",
        returns="str",
        return_description="A handle for the heated sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample being heated."),
            ActionArgument("temperature_c", "float", "Target temperature in Celsius."),
            ActionArgument("duration_min", "float", "Heating time in minutes."),
            ActionArgument("device", "str", "Heating device or bath used in the step."),
        ),
    ),
    "cool_sample": ActionSpec(
        name="cool_sample",
        family="incubate",
        description="Cool or chill a sample to a target temperature.",
        returns="str",
        return_description="A handle for the cooled sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample being cooled."),
            ActionArgument("temperature_c", "float", "Target cooling temperature in Celsius."),
            ActionArgument("duration_min", "float", "Cooling time in minutes."),
            ActionArgument("device", "str", "Cooling device such as ice bath, refrigerator, or freezer."),
        ),
    ),
    "set_thermal_mixer": ActionSpec(
        name="set_thermal_mixer",
        family="incubate",
        description="Process a sample in a thermal mixer with specified temperature and agitation.",
        returns="str",
        return_description="A handle for the thermomixed sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample loaded into the thermal mixer."),
            ActionArgument("temperature_c", "float", "Temperature setting in Celsius."),
            ActionArgument("speed_rpm", "int", "Mixing speed in RPM."),
            ActionArgument("duration_min", "float", "Program duration in minutes."),
        ),
    ),
    "run_thermal_cycler": ActionSpec(
        name="run_thermal_cycler",
        family="incubate",
        description="Run a thermal cycler program on a loaded plate or tube strip.",
        returns="str",
        return_description="A handle for the thermocycled product.",
        arguments=(
            ActionArgument("plate", "str", "Loaded plate or strip processed by the cycler."),
            ActionArgument("program_name", "str", "Program identifier or stage name."),
            ActionArgument("cycles", "int", "Number of program cycles."),
            ActionArgument("lid_temperature_c", "float", "Heated lid temperature in Celsius."),
        ),
    ),
    "dry_sample": ActionSpec(
        name="dry_sample",
        family="incubate",
        description="Dry a sample under a defined method and temperature.",
        returns="str",
        return_description="A handle for the dried sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample being dried."),
            ActionArgument("method", "str", "Drying method such as air dry, oven dry, or vacuum dry."),
            ActionArgument("temperature_c", "float", "Drying temperature in Celsius."),
            ActionArgument("duration_min", "float", "Drying time in minutes."),
        ),
    ),
    "store_sample": ActionSpec(
        name="store_sample",
        family="incubate",
        description="Store a processed sample for later use.",
        returns="str",
        return_description="A handle for the stored sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample being stored."),
            ActionArgument("temperature_c", "float", "Storage temperature in Celsius."),
            ActionArgument("duration_h", "float", "Storage duration in hours."),
            ActionArgument("container", "str", "Storage vessel or storage location."),
        ),
    ),
    "centrifuge_sample": ActionSpec(
        name="centrifuge_sample",
        family="centrifuge",
        description="Centrifuge a sample at a defined speed, duration, and temperature.",
        returns="str",
        return_description="A handle for the centrifuged sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample or tube placed in the centrifuge."),
            ActionArgument("speed_xg", "int", "Relative centrifugal force in x g."),
            ActionArgument("duration_min", "float", "Spin time in minutes."),
            ActionArgument("temperature_c", "float", "Centrifuge chamber temperature in Celsius."),
        ),
    ),
    "load_centrifuge_rotor": ActionSpec(
        name="load_centrifuge_rotor",
        family="centrifuge",
        description="Load a tube or vessel into a centrifuge rotor position.",
        returns="str",
        return_description="A handle for the loaded rotor setup.",
        arguments=(
            ActionArgument("instrument", "str", "Centrifuge instrument identifier."),
            ActionArgument("tube", "str", "Tube or vessel being loaded."),
            ActionArgument("slot", "str", "Rotor slot or bucket position."),
            ActionArgument("balance_with", "str", "Balancing tube or balancing condition."),
        ),
    ),
    "wash_sample": ActionSpec(
        name="wash_sample",
        family="wash",
        description="Wash a bulk sample or solid phase with a named buffer.",
        returns="str",
        return_description="A handle for the washed sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample to wash."),
            ActionArgument("wash_buffer", "str", "Buffer or solvent used for washing."),
            ActionArgument("volume_ul", "float", "Wash volume in microliters."),
            ActionArgument("repeat_index", "int", "Index of the current wash repetition."),
        ),
    ),
    "wash_pellet": ActionSpec(
        name="wash_pellet",
        family="wash",
        description="Wash a centrifuged pellet while preserving the pellet fraction.",
        returns="str",
        return_description="A handle for the washed pellet.",
        arguments=(
            ActionArgument("pellet", "str", "Pellet or bead pellet to wash."),
            ActionArgument("wash_buffer", "str", "Buffer or solvent used for washing."),
            ActionArgument("volume_ul", "float", "Wash volume in microliters."),
            ActionArgument("repeat_index", "int", "Index of the current wash repetition."),
        ),
    ),
    "discard_supernatant": ActionSpec(
        name="discard_supernatant",
        family="wash",
        description="Discard or decant the supernatant after phase separation or centrifugation.",
        returns="str",
        return_description="A handle for the retained solid phase or pellet.",
        arguments=(
            ActionArgument("sample", "str", "Centrifuged or separated sample."),
            ActionArgument("volume_ul", "float", "Approximate supernatant volume removed."),
            ActionArgument("method", "str", "Removal method such as decanting or pipetting."),
            ActionArgument("retain_pellet", "bool", "Whether the solid phase is intentionally retained."),
        ),
    ),
    "aspirate_supernatant": ActionSpec(
        name="aspirate_supernatant",
        family="wash",
        description="Aspirate the upper liquid phase while preserving the lower phase or pellet.",
        returns="str",
        return_description="A handle for the remaining sample after aspiration.",
        arguments=(
            ActionArgument("sample", "str", "Separated sample to aspirate from."),
            ActionArgument("volume_ul", "float", "Aspirated volume in microliters."),
            ActionArgument("tool", "str", "Pipette or aspiration tool."),
            ActionArgument("preserve_pellet", "bool", "Whether the pellet or lower phase must be preserved."),
        ),
    ),
    "resuspend_pellet": ActionSpec(
        name="resuspend_pellet",
        family="wash",
        description="Resuspend a pellet in a named buffer or solution.",
        returns="str",
        return_description="A handle for the resuspended pellet or bead slurry.",
        arguments=(
            ActionArgument("pellet", "str", "Pellet or bead fraction being resuspended."),
            ActionArgument("buffer", "str", "Resuspension buffer or solvent."),
            ActionArgument("volume_ul", "float", "Resuspension volume in microliters."),
            ActionArgument("method", "str", "Resuspension method such as pipetting or gentle vortexing."),
        ),
    ),
    "filter_sample": ActionSpec(
        name="filter_sample",
        family="separate",
        description="Filter a sample through a filter or membrane into a destination vessel.",
        returns="str",
        return_description="A handle for the filtered sample.",
        arguments=(
            ActionArgument("sample", "str", "Input sample passed through the filter."),
            ActionArgument("filter_type", "str", "Filter medium or membrane type."),
            ActionArgument("pore_size_um", "float", "Filter pore size in micrometers."),
            ActionArgument("destination", "str", "Destination vessel after filtration."),
        ),
    ),
    "magnetic_separate": ActionSpec(
        name="magnetic_separate",
        family="separate",
        description="Separate a bead-based sample on a magnetic rack.",
        returns="str",
        return_description="A handle for the magnetically separated sample.",
        arguments=(
            ActionArgument("sample", "str", "Sample containing magnetic beads."),
            ActionArgument("rack", "str", "Magnetic rack identifier."),
            ActionArgument("duration_min", "float", "Magnetic separation time in minutes."),
            ActionArgument("collect_phase", "str", "Phase to retain after separation."),
        ),
    ),
    "place_on_magnet": ActionSpec(
        name="place_on_magnet",
        family="separate",
        description="Place a vessel on a magnetic rack before aspirating or collecting phases.",
        returns="str",
        return_description="A handle for the sample after magnetic placement.",
        arguments=(
            ActionArgument("sample", "str", "Sample vessel placed on the magnet."),
            ActionArgument("rack", "str", "Magnetic rack identifier."),
            ActionArgument("duration_min", "float", "Standing time on the magnet in minutes."),
            ActionArgument("orientation", "str", "Required vessel orientation on the rack."),
        ),
    ),
    "measure_signal": ActionSpec(
        name="measure_signal",
        family="measure",
        description="Measure a sample with an assay-specific readout.",
        returns="str",
        return_description="A handle for the measurement result.",
        arguments=(
            ActionArgument("sample", "str", "Sample or plate being measured."),
            ActionArgument("assay", "str", "Measurement assay or modality."),
            ActionArgument("wavelength_nm", "int", "Measurement wavelength in nanometers."),
            ActionArgument("replicate_n", "int", "Number of technical replicates included in the readout."),
        ),
    ),
    "record_measurement": ActionSpec(
        name="record_measurement",
        family="measure",
        description="Record a derived metric or QC observation from a processed sample.",
        returns="str",
        return_description="A handle for the recorded measurement entry.",
        arguments=(
            ActionArgument("sample", "str", "Sample or output being documented."),
            ActionArgument("metric", "str", "Named metric being recorded."),
            ActionArgument("unit", "str", "Unit of the recorded metric."),
            ActionArgument("note", "str", "Short observation or QC note."),
        ),
    ),
    "open_device": ActionSpec(
        name="open_device",
        family="device",
        description="Open a laboratory device or access panel.",
        returns="str",
        return_description="A handle for the opened device state.",
        arguments=(
            ActionArgument("device", "str", "Device being opened."),
            ActionArgument("target", "str", "Door, lid, drawer, or panel being opened."),
            ActionArgument("mode", "str", "Operation mode or latch condition."),
        ),
    ),
    "close_device": ActionSpec(
        name="close_device",
        family="device",
        description="Close a laboratory device or access panel.",
        returns="str",
        return_description="A handle for the closed device state.",
        arguments=(
            ActionArgument("device", "str", "Device being closed."),
            ActionArgument("target", "str", "Door, lid, drawer, or panel being closed."),
            ActionArgument("mode", "str", "Operation mode or latch condition."),
        ),
    ),
    "press_button": ActionSpec(
        name="press_button",
        family="device",
        description="Press a named button or switch on a laboratory device.",
        returns="str",
        return_description="A handle for the device state after button activation.",
        arguments=(
            ActionArgument("device", "str", "Device containing the button."),
            ActionArgument("button", "str", "Button or switch identifier."),
            ActionArgument("hold_s", "float", "Button hold time in seconds."),
            ActionArgument("repeat_n", "int", "Number of button presses."),
        ),
    ),
    "open_thermal_cycler_lid": ActionSpec(
        name="open_thermal_cycler_lid",
        family="device",
        description="Open the heated lid of a thermal cycler before loading or unloading samples.",
        returns="str",
        return_description="A handle for the open thermal cycler state.",
        arguments=(
            ActionArgument("instrument", "str", "Thermal cycler identifier."),
            ActionArgument("latch_state", "str", "Latch or lock condition required for opening."),
            ActionArgument("plate", "str", "Plate or strip associated with the lid operation."),
        ),
    ),
    "close_thermal_cycler_lid": ActionSpec(
        name="close_thermal_cycler_lid",
        family="device",
        description="Close and secure the heated lid of a thermal cycler.",
        returns="str",
        return_description="A handle for the closed thermal cycler state.",
        arguments=(
            ActionArgument("instrument", "str", "Thermal cycler identifier."),
            ActionArgument("latch_state", "str", "Latch or lock condition after closing."),
            ActionArgument("plate", "str", "Plate or strip associated with the lid operation."),
        ),
    ),
    "pick_container": ActionSpec(
        name="pick_container",
        family="manipulate",
        description="Pick up a named vessel or object from the workspace.",
        returns="str",
        return_description="A handle for the picked object.",
        arguments=(
            ActionArgument("object_id", "str", "Object or vessel to pick."),
            ActionArgument("grasp_site", "str", "Preferred grasp site."),
            ActionArgument("approach_pose", "str", "Approach pose or direction."),
        ),
    ),
    "place_container": ActionSpec(
        name="place_container",
        family="manipulate",
        description="Place a picked object into a named target site.",
        returns="str",
        return_description="A handle for the placed object state.",
        arguments=(
            ActionArgument("object_id", "str", "Object or vessel being placed."),
            ActionArgument("target_site", "str", "Placement destination."),
            ActionArgument("orientation", "str", "Required placement orientation."),
        ),
    ),
    "pour_liquid": ActionSpec(
        name="pour_liquid",
        family="manipulate",
        description="Pour liquid from one open container into another.",
        returns="str",
        return_description="A handle for the destination container after pouring.",
        arguments=(
            ActionArgument("source_container", "str", "Container being tilted."),
            ActionArgument("target_container", "str", "Container receiving the liquid."),
            ActionArgument("tilt_angle_deg", "float", "Tilt angle in degrees."),
            ActionArgument("duration_s", "float", "Pouring duration in seconds."),
        ),
    ),
    "seal_plate": ActionSpec(
        name="seal_plate",
        family="device",
        description="Seal a loaded plate before thermal cycling or storage.",
        returns="str",
        return_description="A handle for the sealed plate.",
        arguments=(
            ActionArgument("plate", "str", "Plate being sealed."),
            ActionArgument("seal_type", "str", "Seal film, foil, or cap strip type."),
            ActionArgument("pressure", "str", "Applied sealing pressure or sealing style."),
            ActionArgument("duration_s", "float", "Sealing duration in seconds."),
        ),
    ),
}


STEP_FAMILY_TO_ACTIONS: dict[str, tuple[str, ...]] = {
    "transfer": ("add_reagent", "aliquot_sample", "transfer_liquid", "collect_fraction", "load_plate"),
    "mix": ("mix_sample", "vortex_mix", "stir_with_rod", "shake_container"),
    "incubate": ("incubate_sample", "heat_sample", "cool_sample", "set_thermal_mixer", "run_thermal_cycler", "dry_sample", "store_sample"),
    "centrifuge": ("centrifuge_sample",),
    "wash": ("wash_sample", "wash_pellet", "discard_supernatant", "aspirate_supernatant", "resuspend_pellet"),
    "separate": ("filter_sample", "magnetic_separate", "place_on_magnet", "collect_fraction"),
    "measure": ("measure_signal", "record_measurement"),
    "device": ("open_device", "close_device", "press_button", "open_thermal_cycler_lid", "close_thermal_cycler_lid", "seal_plate"),
    "manipulate": ("pick_container", "place_container", "pour_liquid"),
}


PROTOCOL_LEVEL_DISTRACTOR_ACTIONS: tuple[str, ...] = (
    "add_reagent",
    "transfer_liquid",
    "mix_sample",
    "incubate_sample",
    "centrifuge_sample",
    "discard_supernatant",
    "resuspend_pellet",
    "measure_signal",
)


LOW_LEVEL_ACTIONS: tuple[str, ...] = (
    "load_centrifuge_rotor",
    "pick_container",
    "place_container",
    "pour_liquid",
)


def render_action_definition(spec: ActionSpec) -> str:
    args_signature = ", ".join(f"{arg.name}: {arg.type_hint}" for arg in spec.arguments)
    doc_lines = [
        f'"""{spec.description}',
        "",
        "Args:",
    ]
    for arg in spec.arguments:
        doc_lines.append(f"    {arg.name}: {arg.description}")
    doc_lines.extend(
        [
            "Returns:",
            f"    {spec.return_description}",
            '"""',
        ]
    )
    docstring = "\n    ".join(doc_lines)
    return (
        f"def {spec.name}({args_signature}) -> {spec.returns}:\n"
        f"    {docstring}\n"
        f"    pass\n"
    )


def render_action_pool_code(action_names: list[str]) -> str:
    blocks: list[str] = []
    for name in action_names:
        spec = ACTION_LIBRARY[name]
        blocks.append(render_action_definition(spec))
    return "\n\n".join(blocks).strip() + "\n"
