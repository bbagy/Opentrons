def get_values(*names):
    import json
    _all_values = json.loads("""{"number_of_samples":"24", "p300_multi_mount":"left","p20_multi_mount":"right",
    "SYBR_vol":19, "DNA_vol":1.2,
    "asp_rate_global20":1,"asp_rate_global300":1,"disp_rate_global20":1,"disp_rate_global300":1,
    "drop_threshold":482}""")
    return [_all_values[n] for n in names]


import math
import os
import json
from opentrons.types import Point
from types import MethodType

metadata = {
    'protocolName': 'qPCR Prep in Triplicates 7~9',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'modify': 'Heekuk <hp2523@cumc.columbia.edu>',
    'apiLevel': '2.11'
}


def run(ctx):

    [number_of_samples,  p300_multi_mount, p20_multi_mount,
     SYBR_vol, DNA_vol,
        asp_rate_global20, disp_rate_global20,
        asp_rate_global300, disp_rate_global300,
        drop_threshold
    ] = get_values(  # noqa: F821
        "number_of_samples", 'p300_multi_mount', 'p20_multi_mount',
        "SYBR_vol","DNA_vol",
        "asp_rate_global20", "disp_rate_global20",
        "asp_rate_global300", "disp_rate_global300","drop_threshold")

    # load labware
    mastermix_plate = ctx.load_labware('nest_12_reservoir_15ml', '2','reagent reservoir')
    temp_block = ctx.load_module('temperature module gen2', '3')
    qPCR_plate = temp_block.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 'qPCR plate')
    # DNA_plate = ctx.load_labware('micronics_96_tubes', '6')
    DNA_plate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '6','qPCR plate')

    # tips
    tips300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['8']]

    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['9']]

    # pipettes
    m300 = ctx.load_instrument(
        'p300_multi_gen2', mount=p300_multi_mount, tip_racks=tips300)
    
    m20 = ctx.load_instrument(
        'p20_multi_gen2', mount=p20_multi_mount, tip_racks=tips20)

    m20.flow_rate.aspirate = asp_rate_global20*m20.flow_rate.aspirate
    m20.flow_rate.dispense = disp_rate_global20*m20.flow_rate.dispense
    m300.flow_rate.aspirate = asp_rate_global300*m300.flow_rate.aspirate
    m300.flow_rate.dispense = disp_rate_global300*m300.flow_rate.dispense

    def slow_tip_withdrawal(
     self, speed_limit, well_location):
        if self.mount == 'right':
            axis = 'A'
        else:
            axis = 'Z'
        previous_limit = None
        if axis in ctx.max_speeds.keys():
            for key, value in ctx.max_speeds.items():
                if key == axis:
                    previous_limit = value
        ctx.max_speeds[axis] = speed_limit
        self.move_to(well_location.top())
        ctx.max_speeds[axis] = previous_limit

    # bind additional methods to pipettes
    for pipette_object in [m20, m300]:
        for method in [slow_tip_withdrawal]:
            setattr(
             pipette_object, method.__name__,
             MethodType(method, pipette_object))


    # PROTOCOL
    number_of_samples = int(number_of_samples)

    #DNA_samples = DNA_plate.rows()[0][0:3] 
    #DNA_samples = DNA_plate.rows()[0][3:6] 
    DNA_samples = DNA_plate.rows()[0][6:9] 
    #DNA_samples = DNA_plate.rows()[0][9:12]

    Standard = mastermix_plate.wells()[0]
    SYBR = mastermix_plate.wells()[9:12]


    numberofcontol = math.ceil(24/8)
    Con_samples = qPCR_plate.rows()[0][:numberofcontol]

    PCR_cols = math.ceil(96/8)
    PCR_samples = qPCR_plate.rows()[0][:PCR_cols]

    temp_block.set_temperature(4)
    ctx.pause('Click resume, to start protocol.')

    #=======================================#
    #= Distributing mastermix to PCR plate =#
    #=======================================#
    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 70

    ctx.comment('Distributing mastermix to PCR plate')
    col_per_asp = math.floor(120/SYBR_vol)# it was 180
    num_asp = math.ceil(len(PCR_samples)/col_per_asp)
    dist_sets = [
        PCR_samples[i*col_per_asp:i*col_per_asp+col_per_asp]
        if i < num_asp - 1
        else PCR_samples[i*col_per_asp:]
        for i in range(num_asp)]
    m300.pick_up_tip()
    index = 0
    for dist_set in dist_sets:
        if index == 0:
            SYBR_source = SYBR[0].bottom(-0.7)
        if index == 1:
            SYBR_source = SYBR[2].bottom(-0.7)

        m300.dispense(m300.current_volume, SYBR_source)
        m300.distribute(SYBR_vol, SYBR_source,
                        [PCR.bottom() for PCR in dist_set],
                        air_gap=5, 
                        blow_out=True,
                        blowout_location='source well',
                        new_tip='never')
        m300.blow_out(SYBR_source)
        index += 1

    m300.drop_tip()


    #=======================================#
    #=====         Add control        ======#
    #=======================================#
    # add control
    m20.flow_rate.aspirate = 100
    m20.flow_rate.dispense = 100
    # blow_out
    m20.flow_rate.blow_out = 400
    ctx.comment('Adding control to mastermix')
    airgap = 1
    for Con in Con_samples:   
        m20.pick_up_tip()
        #m20.mix(3, 15, Standard, rate=2)
        m20.aspirate(DNA_vol, Standard.bottom())
        #m20.touch_tip()
        m20.air_gap(airgap)
        m20.dispense(airgap, Con.top())
        m20.dispense(DNA_vol, Con.bottom())
        m20.mix(3, 10, Con.bottom(), rate=0.5)
        m20.blow_out(Con.bottom(3))
        #m20.touch_tip()
        m20.drop_tip()


    #=======================================#
    #=====          Add DNA           ======#
    #=======================================#
    # distribute sample to mastermix
    airgap = 1
    ctx.comment('Distributing sample to mastermix')
    index = 0

    for _ in range(3):
        if index == 0:
            location = PCR_samples[3:6]
            DNA_lacation=DNA_samples[0]
        if index == 1:
            location = PCR_samples[6:9]
            DNA_lacation=DNA_samples[1]
        if index == 2:
            location = PCR_samples[9:12]
            DNA_lacation=DNA_samples[2]
        for d_col in location:
            m20.pick_up_tip()
            m20.aspirate(DNA_vol, DNA_lacation.bottom())
            m20.air_gap(airgap)
            m20.dispense(airgap, d_col.top())
            m20.dispense(DNA_vol, d_col.bottom())
            m20.mix(3, 10, d_col.bottom(), rate=0.5)
            m20.blow_out(d_col.bottom(3))
            #m20.touch_tip()
            m20.drop_tip()
        index += 1
    temp_block.deactivate()