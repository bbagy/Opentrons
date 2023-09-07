def get_values(*names):
    import json
    _all_values = json.loads("""{"p300_multi_mount":"left","volume_final_elution_in_ul":120,"park_tips":true,"tip_track":false,"drop_threshold":216}""")
    return [_all_values[n] for n in names]


import math
import os
import json
from opentrons.types import Point

metadata = {
    'protocolName': 'Qubert DNA plate to Agenta',
    'modify': 'Heekuk <hp2523@cumc.columbia.edu>',
    'apiLevel': '2.11'
}

MAG_HEIGHT = 6.8


def run(ctx):

    [p300_multi_mount, volume_final_elution_in_ul,drop_threshold
     ] = get_values( 
        'p300_multi_mount','volume_final_elution_in_ul','drop_threshold'
        )



    #===    load labware   ===#
    qubert_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '2',
                                   'waste deepwell plate') 
    azenta_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '3', 'elution plate')
    tips300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['5']]                                 

    #===      pipettes      ===#
    m300 = ctx.load_instrument(
        'p300_multi_gen2', mount=p300_multi_mount, tip_racks=tips300)

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}


    #===  pipettes functions ===#
    def pick_up(pip, loc=None):
        pip.pick_up_tip(loc)


    switch = True
    drop_count = 0
    # number of tips trash will accommodate before prompting user to empty

    def drop(pip, loc=None):
        nonlocal switch
        nonlocal drop_count
        if not loc:
            if pip.type == 'multi':
                drop_count += 8
            else:
                drop_count += 1
            if drop_count >= drop_threshold:
                ctx.home()
                ctx.pause('Please empty tips from waste before resuming.')
                drop_count = 0
            side = 30 if switch else -18
            drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
                Point(x=side))
            pip.drop_tip(drop_loc)
            switch = not switch
        else:
            pip.drop_tip(loc)




    #=====================================#
    #transfer supernatant to new PCR plate#
    #=====================================#
    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 100


    wells11 = ['A'+str(i) for i in range(1, 13)]
    for well in wells11:
        pick_up(m300)
        m300.transfer(volume_final_elution_in_ul,
                      qubert_plate[well].bottom(8), azenta_plate[well],
                      new_tip='never')
        m300.blow_out(azenta_plate[well].top(-1))
        drop(m300)



