def get_values(*names):
    import json
    _all_values = json.loads("""{"num_samp":96,"vol_dispensed":500,"delay":0,"asp_height":15,"disp_height":2,"asp_speed":1,"disp_speed":1,"p300_mount":"right"}""")
    return {n: _all_values[n] for n in names}

metadata = {
    'protocolName': 'Supernatant transfer beads tube to 96 Well-Plate',
    'author': 'Heekuk Park <hp2523@cumc.columbia.edu>',
    'source': 'Custom Protocol in Uhlemann Lab',
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
    air_gap = 10  # define air gap here, 10 µl as an example

    if not 1 <= num_samp <= 96:
        raise Exception("Enter a sample number between 1-96")

    # load labware
    tuberack_slots = ['7', '4', '5', '6']  # adjust according to your setup
    tuberacks = [ctx.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', slot, label='Tuberack')
                   for slot in tuberack_slots]
    plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '8')
    tiprack200 = ctx.load_labware('opentrons_96_tiprack_300ul', '2')

    # load instrument
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount, tip_racks=[tiprack200])
    p300.well_bottom_clearance.aspirate = asp_height
    p300.well_bottom_clearance.dispense = disp_height

    # get tubes from each tuberack individually, processing all tubes in a row before moving to the next row
    tubes = []
    for tuberack in tuberacks:
        for row in tuberack.rows():
            tubes.extend(row)

    # protocol
    for samp, dest in zip(tubes, plate.wells()):
        p300.pick_up_tip()

        vol_remaining = vol_dispensed
        while vol_remaining > 0:
            vol = min(vol_remaining, 270 - air_gap)  # Limiting the volume to 250µl minus air gap
            p300.aspirate(vol, samp, rate=asp_speed)
            p300.air_gap(air_gap)  # Create an air gap after aspiration
            p300.dispense(vol + air_gap, dest, rate=disp_speed)
            p300.blow_out(dest)  # Blow out to ensure complete dispensing
            ctx.delay(seconds=delay)

            vol_remaining -= vol  # correctly decrement the remaining volume

        p300.drop_tip()
