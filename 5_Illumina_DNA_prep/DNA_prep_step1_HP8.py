def get_values(*names):
    import json
    _all_values = json.loads("""{"p300_multi_mount":"left","p20_multi_mount":"right",
    "number_of_samples":96,"mix_TWB":true,"reagent_plate_bottom":-1.6,
    "vol_of_TB":5, "vol_of_BLT":5, "vol_of_TSB":5, "vol_TWB":35, "vol_EPM":20,
    "Tagment_Genomic_DNA_min":14, "TSB_min":15,"mag_inc_min":1,
    "park_tips":true,"tip_track":false,"drop_threshold":482}""")
    return [_all_values[n] for n in names]


import math
import os
import json
from opentrons.types import Point

metadata = {
    'protocolName': 'Illumina DNA prep kit before indexing',
    'modify': 'Heekuk <hp2523@cumc.columbia.edu>',
    'date' : '20230322',
    'apiLevel': '2.11'
}

MAG_HEIGHT = 6.8


def run(ctx):
    [p300_multi_mount, p20_multi_mount, number_of_samples, 
     vol_of_TB, vol_of_BLT,vol_of_TSB,vol_TWB, vol_EPM,reagent_plate_bottom,
     Tagment_Genomic_DNA_min,TSB_min,mag_inc_min,
     vol_TWB, mix_TWB, park_tips, tip_track,
     drop_threshold] = get_values(  # noqa: F821
        'p300_multi_mount', 'p20_multi_mount', 'number_of_samples', 
        'vol_of_TB', 'vol_of_BLT','vol_of_TSB','vol_TWB', 'vol_EPM','reagent_plate_bottom',
        'Tagment_Genomic_DNA_min','TSB_min','mag_inc_min',
        'vol_TWB', 'mix_TWB', 'park_tips', 'tip_track',
        'drop_threshold')
    
    #================================#
    #===       load labware       ===#
    #================================#
    # modules and plates
    DNA_plate = ctx.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', '6', 'elution plate')
    
    temp_block = ctx.load_module('temperature module gen2', '3')
    PCR_plate = temp_block.load_labware(
        'biorad_96_wellplate_200ul_pcr', 'temperature plate')

    magdeck = ctx.load_module('magnetic module gen2', '1')
    mag_plate = magdeck.load_labware(
        'nest_96_wellplate_100ul_pcr_full_skirt', 'magnetic plate')
    
    # sample setup
    num_cols = math.ceil(number_of_samples/8)
    mag_samples = mag_plate.rows()[0][:num_cols]
    PCR_samples = PCR_plate.rows()[0][:num_cols]
    DNA_samples = DNA_plate.rows()[0][:num_cols]


    # reagents
    res = ctx.load_labware('usascientific_12_reservoir_22ml', '2', 'reagent reservoir')
    TWB = res.wells()[11]
    
    # reagent_plate = ctx.load_labware('biorad_96_wellplate_200ul_pcr', '5','reagent reservoir')
    
    reagent_plate = ctx.load_labware('nest_12_reservoir_15ml', '5','reagent reservoir')

    BLT = reagent_plate.wells()[0]
    TB = reagent_plate.wells()[2]
    TSB = reagent_plate.wells()[4]
    EPM = reagent_plate.wells()[9:12]

    # waste
    waste_plate = ctx.load_labware('nest_96_wellplate_2ml_deep', '4',
                                   'waste deepwell plate')
    
    waste = [chan.top(-5) for chan in waste_plate.rows()[0][:num_cols]]

    # tips
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['8','9','11']]

    tips300 = [
        ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['10']]

    # pipettes
    m300 = ctx.load_instrument(
        'p300_multi_gen2', mount=p300_multi_mount, tip_racks=tips300)
    
    m20 = ctx.load_instrument(
        'p20_multi_gen2', mount=p20_multi_mount, tip_racks=tips20)

    


    if park_tips:
        rack = ctx.load_labware(
            'opentrons_96_tiprack_300ul', '7', 'tiprack for parking')
        parking_spots = rack.rows()[0][:num_cols]
        
    else:
        rack = ctx.load_labware(
            'opentrons_96_tiprack_300ul', '7', '200µl filtertiprack')
        parking_spots = [None for none in range(12)]

    tips300.insert(0, rack)

    #================================#
    #===   Others calculations    ===#
    #================================#
    # Check number of samples 
    if number_of_samples > 96 or number_of_samples < 1:
        raise Exception('Invalid number of samples.')

    num_cols = math.ceil(number_of_samples/8)

    # process 4 columns at a time
    numberSet = 4 # was 4
    num_drying_sets = math.ceil(num_cols/numberSet) 

    drying_sets = [
        mag_samples[i*numberSet:i*numberSet+numberSet] if i < num_drying_sets - 1
        else mag_samples[i*numberSet:]
        for i in range(num_drying_sets)]
    
    parking_sets = [
        parking_spots[i*numberSet:i*numberSet+numberSet] if i < num_drying_sets - 1
        else parking_spots[i*numberSet:]
        for i in range(num_drying_sets)]
    
    waste_sets = [
        waste[i*numberSet:i*numberSet+numberSet] if i < num_drying_sets - 1
        else waste[i*numberSet:]
        for i in range(num_drying_sets)]

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}
    folder_path = '/data/bead_cleanup'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                for pip in tip_log:
                    if pip.name in data:
                        tip_log[pip]['count'] = data[pip.name]
                    else:
                        tip_log[pip]['count'] = 0
        else:
            for pip in tip_log:
                tip_log[pip]['count'] = 0
    else:
        for pip in tip_log:
            tip_log[pip]['count'] = 0

    for pip in tip_log:
        if pip.type == 'multi':
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.rows()[0]]
        else:
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.wells()]
        tip_log[pip]['max'] = len(tip_log[pip]['tips'])


    # tips pick up function 
    def pick_up(pip, loc=None):
        if tip_log[pip]['count'] == tip_log[pip]['max'] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log[pip]['count'] = 0
        if loc:
            pip.pick_up_tip(loc)
            return loc
        else:
            loc = tip_log[pip]['tips'][tip_log[pip]['count']]
            # Add this condition to skip parking spots when picking up tips
            while loc in parking_spots:
                tip_log[pip]['count'] += 1
                loc = tip_log[pip]['tips'][tip_log[pip]['count']]

            pip.pick_up_tip(loc)
            tip_log[pip]['count'] += 1
            return loc

    switch = True
    drop_count = 0
    # number of tips trash will accommodate before prompting user to empty

    # tips drop off function 
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

    # mix beads
    ctx.max_speeds['A'] = 50
    ctx.max_speeds['Z'] = 50

    # blow_out
    m20.flow_rate.blow_out = 250
    m300.flow_rate.blow_out = 200
    magdeck.disengage()
    #=====================================#
    #==  Step1 Add TB to PCR plate      ==#
    #=====================================#
    #TB_loc = None
    col_per_asp = math.floor(33/vol_of_TB)# it was 180
    num_asp = math.ceil(len(PCR_samples)/col_per_asp)
    dist_sets = [
        PCR_samples[i*col_per_asp:i*col_per_asp+col_per_asp]
        if i < num_asp - 1
        else PCR_samples[i*col_per_asp:]
        for i in range(num_asp)]
    TB_loc = pick_up(m20)
    for dist_set in dist_sets:
        TB.hight = TB.bottom(reagent_plate_bottom)
        m20.dispense(m20.current_volume, TB.hight)
        m20.distribute(vol_of_TB, TB,
                        [PCR.bottom(-4.3) for PCR in dist_set],
                        blow_out=True,
                        blowout_location='source well',
                        new_tip='never')
        
        m20.blow_out(TB.bottom())

    # drop(m20,TB_loc)

    #=====================================#
    #== Step2 Add BLT to DNA plate       =#
    #=====================================#
    #BLT_loc = None
    first_dna_sample = True

    for d, PCR in zip(DNA_samples, PCR_samples):    
        if not first_dna_sample:
            BLT_loc = pick_up(m20)
        else:
            BLT_loc = TB_loc
            first_dna_sample = False
            
        m20.mix(5, vol_of_BLT, BLT.bottom())
        m20.blow_out(BLT.top(-5))
        m20.flow_rate.aspirate = 40
        m20.flow_rate.dispense = 100
        m20.transfer(vol_of_BLT, BLT, d.bottom(), new_tip='never')
        m20.blow_out(d.top(-2))
        
        # DNA plate  to PCR plate
        m20.flow_rate.aspirate = 20
        m20.transfer(vol_of_BLT+15,
                      d.bottom(0), PCR,
                      new_tip='never')
        
        for _ in range(5):
            m20.flow_rate.aspirate = 70
            m20.flow_rate.dispense = 100
            m20.mix(1, vol_of_BLT+7, PCR.bottom(-4))
            #m20.aspirate(vol_of_BLT+7, PCR.bottom(-4))
            #m20.dispense(vol_of_BLT+7, PCR.center())
        m20.blow_out(PCR.top(-5))
        m20.touch_tip()

        drop(m20,BLT_loc)

    # ADD TEMPERATURE
    ctx.pause('Seal the plate.')
    #temp_block.set_temperature(55)
    #ctx.delay(minutes=Tagment_Genomic_DNA_min, msg='Incubating off \
#Tagment Genomic DNA (TAG) for ' + str(Tagment_Genomic_DNA_min) + ' minutes.')

    #temp_block.set_temperature(20)
    # ctx.delay(minutes=3, msg='Incubating off \
    # After Tagment Genomic DNA (TAG) for ' + str(3) + ' minutes.')
    ctx.pause('Unseal the plate.')

    #=====================================#
    #== Step3 Add TSB to PCR plate       =#
    #=====================================#
    #TSB_loc = None
    # count = 0
    for PCR in PCR_samples:
        TSB_loc = pick_up(m20)
        m20.transfer(vol_of_TSB, TSB.bottom(reagent_plate_bottom), PCR.bottom(), new_tip='never')
        m20.blow_out(PCR.top(-2))
        for _ in range(5):
            m20.flow_rate.aspirate = 70
            m20.flow_rate.dispense = 100
            m20.mix(1, vol_of_TSB+7, PCR.bottom(-4))
            #m20.aspirate(vol_of_TSB+10, PCR.bottom(-4))
            #m20.dispense(vol_of_TSB+10, PCR.center())
        m20.blow_out(PCR.top(-2))
        m20.touch_tip()
        #count += 1
        drop(m20,TSB_loc)
        #if count == 12:
        #    drop(m20)
        #else:
        #    drop(m20,TSB_loc)


    # ADD TEMPERATURE
    ctx.pause('Seal the plate.')
    #temp_block.set_temperature(37)
    #ctx.delay(minutes=TSB_min, msg='Incubating off \
#TSB for ' + str(TSB_min) + ' minutes.')
    # ctx.delay(minutes=3, msg='Incubating off \
    # After TSB for ' + str(3) + ' minutes.')
    #temp_block.set_temperature(20)     
    ctx.pause('Unseal the plate.')
    #temp_block.deactivate()
    
    # pipettes speed
    m300.flow_rate.aspirate = 100
    m300.flow_rate.dispense = 100

    #=====================================#
    #== Step4 PCR plate to mag plate    ==#
    #=====================================#
    magdeck.disengage()

    for PCR, m,p in zip(PCR_samples, mag_samples, parking_spots):
        pick_up(m300, p)
        # PCR plate to mag plate
        m300.mix(5, vol_of_TSB+7, PCR.bottom(-4))
        m300.flow_rate.aspirate = 20
        m300.transfer(vol_of_TB + vol_of_BLT+ vol_of_TSB + 20,
                      PCR.bottom(-4.9), m,
                      new_tip='never')
        m300.blow_out(m.top(-2))
        m300.touch_tip()
        
        drop(m300, p)

    #=====================================#
    #== Step5 remove supernatant        ==# remove 3 and add TWB 3
    #=====================================#
    # pipettes speed
    TWB_loc = None
    EPM_tip = None
    for wash in range(3):
        m300.flow_rate.aspirate = 50
        m300.flow_rate.dispense = 100

        magdeck.engage(height=MAG_HEIGHT)
        ctx.delay(minutes=mag_inc_min, msg='Incubating \
    on magnet for ' + str(mag_inc_min) + ' minutes.')

        # remove supernatant
        for set_ind, (sample_set, parking_set, waste_set) in enumerate(
                zip(drying_sets, parking_sets, waste_sets)):
            m300.flow_rate.aspirate = 20
            for m, p, w in zip(sample_set, parking_set, waste_set):
                pick_up(m300, p)
                m300.aspirate(vol_of_TB + vol_of_BLT+ vol_of_TSB +25, m.bottom(0.5))
                m300.air_gap(5)
                m300.dispense(200, w, rate=0.7)
                m300.blow_out(w)
                m300.air_gap(5)
                drop(m300,p) # add p 
            m300.flow_rate.aspirate = 100
            # add TWB
            # m300.pick_up_tip()

            if wash == 0:
                TWB_loc = pick_up(m300)
            else:
                pick_up(m300)
                #pick_up(m300, TWB_loc)

            # custom distribution
            col_per_asp = math.floor(150/vol_TWB)# it was 180
            num_asp = math.ceil(len(sample_set)/col_per_asp)
            dist_sets = [
                sample_set[i*col_per_asp:i*col_per_asp+col_per_asp]
                if i < num_asp - 1
                else sample_set[i*col_per_asp:]
                for i in range(num_asp)]
        
            for dist_set in dist_sets:
                TWB_source = TWB.bottom(-0.7)
                m300.dispense(m300.current_volume, TWB_source)
                m300.distribute(vol_TWB, TWB_source,
                                [m.top(2) for m in dist_set],
                                air_gap=10, 
                                blow_out=True,
                                blowout_location='source well',
                                new_tip='never')
                m300.air_gap(10)

            m300.blow_out(TWB)

            if wash == 2:
                drop(m300)
            else:
                drop(m300)

        if wash == 2:
            magdeck.engage(height=MAG_HEIGHT)
        else:
            if mix_TWB:
                magdeck.disengage()
                for m, p in zip(mag_samples, parking_spots):
                    pick_up(m300, p)
                    m300.mix(5, vol_TWB*0.8, m)
                    m300.blow_out(m.top())
                    drop(m300, p)
                
        #======== Add EPM to mag plate    
        if wash == 2:
            magdeck.engage(height=MAG_HEIGHT)
            ctx.delay(minutes=mag_inc_min, msg='Incubating \
    on magnet for ' + str(mag_inc_min) + ' minutes.')
            
            ctx.pause('Click resume, when you are ready for EPM mix.')
            m300.flow_rate.aspirate = 100
            m300.flow_rate.dispense = 200
            chan_ind = 0
            vol_track = 0

            max_vol_per_chan = 100
            
            for set_ind, (sample_set, parking_set, waste_set) in enumerate(
                    zip(drying_sets, parking_sets, waste_sets)):
                m300.flow_rate.aspirate = 20
                for m, p, w in zip(sample_set, parking_set, waste_set):
                    pick_up(m300, p)
                    m300.aspirate(vol_TWB +30, m.bottom(0.5))
                    m300.air_gap(5)
                    m300.dispense(250, w, rate=0.5)
                    m300.blow_out(w)
                    m300.air_gap(5)
                    drop(m300,p) # add p 
                m300.flow_rate.aspirate = 100

                # m300.pick_up_tip()
                pick_up(m300, EPM_tip)
                # custom distribution
                col_per_asp = math.floor(65/vol_EPM)# it was 180
                num_asp = math.ceil(len(sample_set)/col_per_asp)
                dist_sets = [
                    sample_set[i*col_per_asp:i*col_per_asp+col_per_asp]
                    if i < num_asp - 1
                    else sample_set[i*col_per_asp:]
                    for i in range(num_asp)]
                
                for dist_set in dist_sets:
                    if vol_track + vol_EPM > max_vol_per_chan:
                        chan_ind += 2
                        vol_track = 0

                    source = EPM[chan_ind]
                    
                    for m in dist_set:
                        m300.aspirate(vol_EPM, source.bottom(-1))
                        m300.air_gap(3)
                        m300.dispense(vol_EPM+30, m.top(2), rate=0.7)
                        m300.blow_out(m)
                        m300.air_gap(3)    
                        vol_track += vol_EPM

                if set_ind == len(sample_set) - 1:
                    drop(m300)
                else:
                    drop(m300, EPM_tip)

    magdeck.disengage()

    # temp_block.set_temperature(4) 
    #=====================================#
    #== Step6 PCR plate to mag plate    ==#
    #=====================================#
    magdeck.disengage()

    for m, PCR, p in zip(mag_samples, PCR_samples, parking_spots):
        pick_up(m300,p)
        m300.flow_rate.aspirate = 70
        m300.mix(10, vol_EPM*0.8, m)
        m300.transfer(vol_EPM+15,
                      m.bottom(0), PCR,
                      new_tip='never')
        m300.blow_out(PCR.top(-2))
        
        drop(m300,p)

    magdeck.disengage()
    temp_block.deactivate()
