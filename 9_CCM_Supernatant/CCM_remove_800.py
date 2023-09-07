
def get_values(*names):
    import json
    _all_values = json.loads("""{
        "asp_height":4.5,
        "transfer_vol":800.0,
        "asp_speed":100,
        "disp_speed":100,
        "disp_height":10,
        "max_vol":300
    }""")
    return [_all_values[n] for n in names]

metadata = {
    'protocolName': 'CCM_remove_800',
    'author': 'Heekuk Park <sakib.hossain@opentrons.com>',
    'source': 'Custom Protocol in Uhlemann Lab',
    'apiLevel': '2.8'
}

def run(protocol):
    [asp_speed, disp_speed, asp_height, disp_height, transfer_vol, max_vol] = get_values('asp_speed', 'disp_speed', 'asp_height', 'disp_height', 'transfer_vol', 'max_vol')

    # load Labware
    plate1 = protocol.load_labware('nest_96_wellplate_2ml_deep', 5, 'Starting plate')
    plate2 = protocol.load_labware('nest_96_wellplate_2ml_deep', 8, 'Destination')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 2)

    # load instrument
    m300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack])

    # Get sample columns
    plate1_wells = plate1.rows()[0]
    plate2_wells = plate2.rows()[0]

    # Flow Rates
    m300.flow_rate.aspirate = asp_speed
    m300.flow_rate.dispense = disp_speed
    air_gap=10

    # Transfer transfer_vol uL to Plate 2
    for p1_well, p2_well in zip(plate1_wells, plate2_wells):
        m300.pick_up_tip()

        remaining_vol = transfer_vol
        while remaining_vol > 0:
            vol_to_transfer = min(remaining_vol, max_vol - air_gap)
            m300.aspirate(vol_to_transfer, p1_well.bottom(z=asp_height))
            m300.air_gap(air_gap)
            m300.dispense(vol_to_transfer, p2_well.bottom(z=disp_height))
            m300.blow_out(p2_well)  # Blow out to ensure complete dispensing
            remaining_vol -= vol_to_transfer

        m300.drop_tip()


