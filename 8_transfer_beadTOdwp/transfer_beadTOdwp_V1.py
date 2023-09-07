def get_values(*names):
    import json
    _all_values = json.loads("""{"num_samp":96,"vol_dispensed":500,"delay":3,"asp_height":50,"disp_height":2,"asp_speed":1,"disp_speed":1,"p300_mount":"right"}""")
    return {n: _all_values[n] for n in names}


metadata = {
    'protocolName': 'Supernatant transfer beads tube to 96 Well-Plate',
    'author': 'Heekuk Park <hp2523@cumc.columbia.edu>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.9'
}


def run(ctx):
    values = get_values("num_samp", "vol_dispensed", "delay", "asp_height", "disp_height", "asp_speed", "disp_speed", "p300_mount")

    num_samp = values["num_samp"]
    vol_dispensed = values["vol_dispensed"]
    delay = values["delay"]
    asp_height = values["asp_height"]
    disp_height = values["disp_height"]
    asp_speed = values["asp_speed"]
    disp_speed = values["disp_speed"]
    p300_mount = values["p300_mount"]

    if not 1 <= num_samp <= 96:
        raise Exception("Enter a sample number between 1-96")

    # load labware
    tuberack_96 = [ctx.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', slot, label='Tuberack')
                   for slot in ['7', '4', '5', '6']]
    plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '8')
    tiprack200 = ctx.load_labware('opentrons_96_filtertiprack_200ul', '2')

    # load instrument
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount, tip_racks=[tiprack200])
    p300.well_bottom_clearance.aspirate = asp_height
    p300.well_bottom_clearance.dispense = disp_height

    tubes = [tube for tuberack in tuberack_96 for tube in tuberack.wells()]
    pip = p300

    # protocol
    for samp, dest in zip(tubes, plate.wells()):
        pip.pick_up_tip()

        vol_remaining = vol_dispensed
        while vol_remaining > 0:
            vol = min(vol_remaining, pip.max_volume)
            pip.aspirate(vol, samp, rate=asp_speed)
            pip.dispense(vol, dest, rate=disp_speed)
            pip.blow_out(dest)  # Blow out to ensure complete dispensing
            ctx.delay(seconds=delay)

            vol_remaining -= vol  # correctly decrement the remaining volume

        pip.drop_tip()
