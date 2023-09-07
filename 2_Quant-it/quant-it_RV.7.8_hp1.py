def get_values(*names):
    import json
    _all_values = json.loads("""{"p20mnt":"right","p300mnt":"left"}""")
    return [_all_values[n] for n in names]







metadata = {
    'protocolName': 'Quant-iT dsDNA Broad-Range Assay Kit(reservoir 7 and 8)',
    'author': 'Heekuk <hp2523@cumc.columbia.edu',
    'source': 'https://protocols.opentrons.com/protocol/42d27b',
    'apiLevel': '2.2'
}


def run(protocol):
    [p300mnt, p20mnt] = get_values(  # noqa: F821
        'p300mnt', 'p20mnt')

    # load labware and pipettes
    tube_plate = protocol.load_labware('micronics_96_tubes', '1')
    aplate = protocol.load_labware('axygen_96_wellplate', '2')
    res = protocol.load_labware('nest_12_reservoir_15ml', '3')

    tips20 = [protocol.load_labware('opentrons_96_tiprack_20ul', '4')]
    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', '5')]

    p300 = protocol.load_instrument('p300_multi_gen2', p300mnt, tip_racks=tips300)
    p20 = protocol.load_instrument('p20_multi_gen2', p20mnt, tip_racks=tips20)


    # Step 1: Add reagent
    wells6 = ['A'+str(i) for i in range(1, 7)]

    p300.pick_up_tip()
    
    for well in wells6:
        p300.transfer(200, res['A7'], aplate[well].top(), new_tip='never')
        p300.air_gap(5)
        p300.blow_out(aplate[well].top())
        
    wells12 = ['A'+str(i) for i in range(7, 13)]
    for well in wells12:
        p300.transfer(200, res['A8'], aplate[well].top(), new_tip='never')
        p300.air_gap(5)
        p300.blow_out(aplate[well].top())

    p300.drop_tip()

    # Step 2: Add DNA
    wells11 = ['A'+str(i) for i in range(2, 13)]
    for well in wells11:
        p20.pick_up_tip()
        p20.transfer(2, tube_plate[well].bottom(z=-3), aplate[well], new_tip='never')
        p20.mix(5,15, aplate[well].bottom(z=2))
        p20.blow_out(aplate[well].top())
        # p20.return_tip()
        p20.drop_tip()
