def get_values(*names):
    import json
    _all_values = json.loads("""{"num_samples":96,"deepwell_type":"nest_96_wellplate_2ml_deep","res_type":"nest_12_reservoir_15ml",
                             "starting_vol":800,
                             "wash1_vol":240,"wash2_vol":240,"wash3_vol":240,"wash4_vol":240,"elution_vol":100,
                             "mix_reps":6,"settling_time":6,"settling_time_for_elution":3,
                             "park_tips":true,"tip_track":true,"flash":true,
                             "include_wash1":true,"include_wash2":true,"include_wash3":true,"include_wash4":true,
                             "include_dry":true,"include_elute":true}""")
    return [_all_values[n] for n in names]


from opentrons.types import Point
import json
import os
import math
import threading
from time import sleep
from opentrons import types

metadata = {
    'protocolName': 'ZymoBIOMIC MagBead DNA/RNA',
    'author': 'Heekuk Park <hp2523@cumc.columbia.edu>',
    'apiLevel': '2.11'
}


"""
Here is where you can modify the magnetic module engage height:
"""
MAG_HEIGHT = 4 # 3.6


# Definitions for deck light flashing
class CancellationToken:
    def __init__(self):
        self.is_continued = False

    def set_true(self):
        self.is_continued = True

    def set_false(self):
        self.is_continued = False


def turn_on_blinking_notification(hardware, pause):
    while pause.is_continued:
        hardware.set_lights(rails=True)
        sleep(1)
        hardware.set_lights(rails=False)
        sleep(1)


def create_thread(ctx, cancel_token):
    t1 = threading.Thread(target=turn_on_blinking_notification,
                          args=(ctx._hw_manager.hardware, cancel_token))
    t1.start()
    return t1




# Start protocol
def run(ctx):
    # Setup for flashing lights notification to empty trash
    cancellationToken = CancellationToken()
    # initialize thread
    thread = None

    [num_samples, deepwell_type, res_type, starting_vol,
    wash1_vol, wash2_vol, wash3_vol, wash4_vol, elution_vol,
     mix_reps, settling_time, settling_time_for_elution, park_tips, tip_track, flash,
     include_wash1, include_wash2, include_wash3, include_wash4,
     include_dry, include_elute] = get_values(  # noqa: F821
        'num_samples','deepwell_type', 'res_type',
        'starting_vol', 'wash1_vol', 'wash2_vol', 'wash3_vol','wash4_vol', 'elution_vol', 
        'mix_reps', 'settling_time', 'settling_time_for_elution', 'park_tips',
        'tip_track', 'flash', 'include_wash1', 'include_wash2',
        'include_wash3', 'include_wash4','include_dry', 'include_elute')

    """
    Here is where you can change the locations of your labware and modules
    (note that this is the recommended configuration)
    """
    magdeck = ctx.load_module('magnetic module gen2', '1')
    magdeck.disengage()
    magplate = magdeck.load_labware(deepwell_type, 'deepwell plate')
    lysateplate = ctx.load_labware(deepwell_type,2, 'lysate plate')
    elutionplate = ctx.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '3') 
    
    
    
    waste = ctx.load_labware('nest_1_reservoir_195ml', '4',
                             'Liquid Waste').wells()[0].top()
                             
    res2 = ctx.load_labware(res_type, '7', 'reagent reservoir 1')
    res1 = ctx.load_labware(res_type, '10', 'reagent reservoir 2')
    
    num_cols = math.ceil(num_samples/8)
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot,
                                '200µl filtertiprack')
               for slot in ['6']]
    if park_tips:
        parkingrack = ctx.load_labware(
            'opentrons_96_tiprack_300ul', '5', 'tiprack for parking')
        parking_spots = parkingrack.rows()[0][:num_cols]
        
        elutionrack = ctx.load_labware(
            'opentrons_96_tiprack_300ul', '8', 'tiprack for parking')
        elution_spots = elutionrack.rows()[0][:num_cols]
    else:
        tips300.insert(0, ctx.load_labware('opentrons_96_tiprack_300ul', '4',
                                           '200µl filtertiprack'))
        parking_spots = [None for none in range(12)]

    # load P300M pipette
    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'left', tip_racks=tips300)

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    """
    Here is where you can define the locations of your reagents.
    """
    pk = res1.wells()[0]
    lys = res1.wells()[1:3]
    etoh = res1.wells()[3:6]
    bead = res1.wells()[6]

    
    wash1 = res2.wells()[:2]
    wash2 = res2.wells()[2:4]
    wash3 = res2.wells()[4:6]
    wash4 = res2.wells()[6:8]
    elution_solution = res2.wells()[8]


    mag_samples_m = magplate.rows()[0][:num_cols]
    lysate_samples_m = lysateplate.rows()[0][:num_cols]
    elution_samples_m = elutionplate.rows()[0][:num_cols]

    magdeck.disengage()  # just in case
    # tempdeck.set_temperature(4)

    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300
    """
    folder_path = '/data/B'
    tip_file_path = folder_path + '/tip_log.json'
    # if tip_track and ctx.is_simulating():    # reversed logic for simulation
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
    """



    def _pick_up(pip, loc=None):
        if tip_log[pip]['count'] == tip_log[pip]['max'] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log[pip]['count'] = 0
        if loc:
            pip.pick_up_tip(loc)
        else:
            pip.pick_up_tip(tip_log[pip]['tips'][tip_log[pip]['count']])
            tip_log[pip]['count'] += 1

    switch = True
    drop_count = 0
    # number of tips trash will accommodate before prompting user to empty
    drop_threshold = 192

    def _drop(pip):
        nonlocal switch
        nonlocal drop_count
        side = 30 if switch else -18
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
            Point(x=side))
        pip.drop_tip(drop_loc)
        switch = not switch
        if pip.type == 'multi':
            drop_count += 8
        else:
            drop_count += 1
        if drop_count >= drop_threshold:
            # Setup for flashing lights notification to empty trash
            if flash:
                if not ctx._hw_manager.hardware.is_simulator:
                    cancellationToken.set_true()
                thread = create_thread(ctx, cancellationToken)
            m300.home()
            ctx.pause('Please empty tips from waste before resuming.')
            ctx.home()  # home before continuing with protocol
            if flash:
                cancellationToken.set_false()  # stop light flashing after home
                thread.join()
            drop_count = 0

    waste_vol = 0
    waste_threshold = 185000

    def remove_supernatant(vol, park=False):

        def _waste_track(vol):
            nonlocal waste_vol
            if waste_vol + vol >= waste_threshold:
                # Setup for flashing lights notification to empty liquid waste
                if flash:
                    if not ctx._hw_manager.hardware.is_simulator:
                        cancellationToken.set_true()
                    thread = create_thread(ctx, cancellationToken)
                m300.home()
                ctx.pause('Please empty liquid waste (slot 11) before \
resuming.')

                ctx.home()  # home before continuing with protocol
                if flash:
                    # stop light flashing after home
                    cancellationToken.set_false()
                    thread.join()

                waste_vol = 0
            waste_vol += vol

        m300.flow_rate.aspirate = 30
        num_trans = math.ceil(vol/300)
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if park:
                _pick_up(m300, spot)
            else:
                _pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.5).move(Point(x=side*2))
            for _ in range(num_trans):
                _waste_track(vol_per_trans)
                if m300.current_volume > 0:
                    # void air gap if necessary
                    m300.dispense(m300.current_volume, m.top())
                m300.move_to(m.center())
                m300.transfer(vol_per_trans, loc, waste, new_tip='never',
                              air_gap=5)
                m300.blow_out(waste)
                m300.air_gap(5)
            # park or drop tip after resuspending
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)
        m300.flow_rate.aspirate = 150

    def resuspend_pellet(well, pip, mvol, reps=2):

        rightLeft = int(str(well).split(' ')[0][1:]) % 2

        center = well.bottom().move(types.Point(x=0, y=0, z=0.1))
        top = [
            well.bottom().move(types.Point(x=-3.8, y=3.8, z=0.1)),# it was 3.8
            well.bottom().move(types.Point(x=3.8, y=3.8, z=0.1))
        ]
        bottom = [
            well.bottom().move(types.Point(x=-2.8, y=-2.8, z=0.1)),# it was 3.8
            well.bottom().move(types.Point(x=2.8, y=-2.8, z=0.1))
        ]

        pip.flow_rate.dispense = 500
        pip.flow_rate.aspirate = 150

        mix_vol = 0.9 * mvol

        pip.move_to(center)
        for _ in range(reps):
            for _ in range(2):
                pip.aspirate(mix_vol, center)
                pip.dispense(mix_vol, top[rightLeft])
            for _ in range(2):
                pip.aspirate(mix_vol, center)
                pip.dispense(mix_vol, bottom[rightLeft])
                    
                
    def wash(vol, source, mix_reps=mix_reps, park=True, resuspend=True):
        if resuspend and magdeck.status == 'engaged':
            magdeck.disengage()

        num_trans = math.ceil(vol/280)
        vol_per_trans = vol/num_trans
        _pick_up(m300)
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):

            # currently unused variables side and loc
            # side = 1 if i % 2 == 0 else -1
            # loc = m.bottom(0.5).move(Point(x=side*2))
            src = source[i//(12//len(source))]
            for n in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, src.top())
                m300.blow_out(src)
                m300.transfer(vol_per_trans, src, m.top(), air_gap=5,
                              new_tip='never')
                m300.blow_out(m)
                m300.air_gap(5)
                if n < num_trans - 1:  # only air_gap if going back to source
                    m300.air_gap(5)

        _drop(m300)


        # resuspend beads in all samples after transferring volume
        if resuspend:
            for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
                if park:
                    _pick_up(m300, spot)
                else:
                    _pick_up(m300)
                resuspend_pellet(m, m300, 180)
                #m300.blow_out(m.top())
                #m300.air_gap(20)
                if park:
                    m300.drop_tip(spot)
                else:
                    _drop(m300)


        if magdeck.status == 'disengaged':
            magdeck.engage(height=MAG_HEIGHT) #height=MAG_HEIGHT

        ctx.delay(minutes=settling_time, msg='Incubating on MagDeck for \
' + str(settling_time) + ' minutes.')

        # remove_supernatant(vol, park=park) # out from the wash protocol


    def elute(vol, park=True):
        """
        `elute` will perform elution from the deepwell extraciton plate to the.

        final clean elutions PCR plate to complete the extraction protocol.
        :param vol (float): The amount of volume to aspirate from the elution
                            buffer source and dispense to each well containing
                            beads.
        :param park (boolean): Whether to save sample-corresponding tips
                               between adding elution buffer and transferring
                               supernatant to the final clean elutions PCR
                               plate.
        """
        # resuspend beads in elution
        if magdeck.status == 'engaged':
            magdeck.disengage()
        for i, (m, spot) in enumerate(zip(mag_samples_m, elution_spots)):
            _pick_up(m300,spot)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.aspirate(vol, elution_solution)
            m300.move_to(m.center())
            m300.dispense(vol, loc)
            # m300.mix(mix_reps, 0.8*vol, loc)
            resuspend_pellet(m, m300, 50)
            m300.blow_out(m.bottom(5))
            m300.air_gap(5)
            if park:
                m300.drop_tip(spot)
            else:
                _drop(m300)

        magdeck.engage(height=MAG_HEIGHT)#height=MAG_HEIGHT
        ctx.delay(minutes=settling_time_for_elution, msg='Incubating on MagDeck for \
' + str(settling_time_for_elution) + ' minutes.')

        for i, (m, e, spot) in enumerate(
                zip(mag_samples_m, elution_samples_m, elution_spots)):
            if park:
                _pick_up(m300, spot)
            else:
                _pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.transfer(vol, loc, e.center(), air_gap=5, new_tip='never')
            m300.blow_out(e.top(-2))
            m300.air_gap(5)
            _drop(m300)
            
    def Transfer_lysate(vol, source, destination, park=True):
        """
        This function will perform a transfer from the source plate to the destination plate.

        Args:
            vol (float): The volume to be transferred.
            source (list): A list of source wells to aspirate from.
            destination (list): A list of destination wells to dispense to.
            park (bool): If True, the pipette will park its tip in a specified parking spot. Defaults to True.

        Returns:
            None
        """

        for i, (src, dest, spot) in enumerate(zip(source, destination, parking_spots)):
            if park:
                _pick_up(m300, spot)
            else:
                _pick_up(m300)
            m300.transfer(vol, src.bottom(5), dest.bottom(), air_gap=5, new_tip='never')
            m300.blow_out(dest.top(-2))
            m300.air_gap(5)
            m300.drop_tip(spot)


    def Proteinase_k(vol, source):
        """
        A function to dispense a particular volume to a series of wells.

        Args:
            vol (float): The volume to be dispensed.
            source (list): A list of source wells to aspirate from.

        Returns:
            None
        """

        # Disengage the magnetic module if it is engaged
        if magdeck.status == 'engaged':
            magdeck.disengage()

        # Calculate the number of distributions required
        num_distrib = math.ceil(vol/270)
        vol_per_distrib = vol/num_distrib

        # Start the distribution process
        _pick_up(m300)

        src = source
        # Mix before the first distribution

        # Distribute to all wells in magplate.
        for n in range(num_distrib):
            m300.distribute(vol_per_distrib, src.bottom(),
                            [m.bottom() for m in mag_samples_m],
                            new_tip='never',
                            blow_out=True,
                            blowout_location='source well')
        _drop(m300)


    def Add_reagent(vol, source):
        if magdeck.status == 'engaged':
            magdeck.disengage()

        num_trans = math.ceil(vol/270)
        vol_per_trans = vol/num_trans
        _pick_up(m300)
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):

            # currently unused variables side and loc
            # side = 1 if i % 2 == 0 else -1
            # loc = m.bottom(0.5).move(Point(x=side*2))
            src = source[i//(12//len(source))]
            for n in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, src.top())
                m300.transfer(vol_per_trans, src, m.top(), air_gap=5,
                              new_tip='never')
                m300.blow_out(m)
                m300.blow_out(src)
                if n < num_trans - 1:  # only air_gap if going back to source
                    m300.air_gap(5)
        _drop(m300)



    def Add_bead(vol, source):
        """
        A function to dispense a particular volume to a series of wells.

        Args:
            vol (float): The volume to be dispensed.
            source (list): A list of source wells to aspirate from.

        Returns:
            None
        """

        # Disengage the magnetic module if it is engaged
        if magdeck.status == 'engaged':
            magdeck.disengage()

        # Calculate the number of distributions required
        num_distrib = math.ceil(vol/200)
        vol_per_distrib = vol/num_distrib

        # Start the distribution process
        _pick_up(m300)

        src = source
        # Mix before the first distribution
        m300.mix(5, m300.max_volume, src.bottom())

        # Distribute to all wells in magplate.
        for n in range(num_distrib):
            m300.distribute(vol_per_distrib, src.bottom(),
                            [m.top() for m in mag_samples_m],
                            new_tip='never',
                            blow_out=True,
                            air_gap=5,
                            blowout_location='source well')

                # If we're not done with all the distributions, re-mix in the source
            if n < num_distrib - 1:
                m300.mix(5, m300.max_volume, src.bottom())

        _drop(m300)


    def flash_control(ctx, flash=True):
        """
        Flashing logic function.

        Parameters:
        - ctx (object): Context object representing the hardware
        - flash (bool): Flag to decide if flashing should occur. Default is True
        """
        thread = None

        if flash:
            if not ctx._hw_manager.hardware.is_simulator:
                cancellationToken.set_true()
                thread = create_thread(ctx, cancellationToken)
            m300.home()
            ctx.pause('Please shake 30min with beads')
            ctx.home()  # home before continuing with protocol
        
            if thread is None:
                thread = create_thread(ctx, cancellationToken)
            cancellationToken.set_false()  # stop light flashing after home
            if thread is not None:
                thread.join()

    # Example usage: flash_control(ctx, True)

    def final_tip_tracker(ctx, tip_track, folder_path='/data/B', tip_file_path='/data/B/tip_log.json', tip_log={}):
        """
        Function to track the final tips used.

        Parameters:
        - ctx (object): Context object representing the hardware
        - tip_track (bool): Flag to decide if tip tracking should occur
        - folder_path (str): Path to the directory where the tip file will be stored. Defaults to '/data/B'.
        - tip_file_path (str): Path to the file where tip data will be saved. Defaults to '/data/B/tip_log.json'.
        - tip_log (dict): Log of the tips used. Default is an empty dictionary.
        """
        
        if tip_track and not ctx.is_simulating():
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            data = {pip: tip_log[pip]['count'] for pip in tip_log}
            with open(tip_file_path, 'w') as outfile:
                json.dump(data, outfile)



    """
    Here is where you can call the methods defined above to fit your specific
    protocol. The normal sequence is:
    """
    
    #=====================================#
    #==   Step1: Adding proteinase k    ==#
    #=====================================#
    
    Proteinase_k(10, pk)
    Transfer_lysate(vol=200, source=lysate_samples_m, destination= mag_samples_m, park=True)
    
    flash_control(ctx, True)
    
    #=======================================#
    #= Step2: Adding lysis buffer and ETOH =#
    #=======================================#
    Add_reagent(200,lys)
    
    flash_control(ctx, True)

    Add_reagent(400, etoh)
    Add_bead(30, bead)

    flash_control(ctx, True)


    #=======================================#
    #= Step3: Remove supernatant           =#
    #=======================================#
    magdeck.engage(height=MAG_HEIGHT) 
    ctx.delay(minutes=10, msg='Incubating on MagDeck for \
' + str(10) + ' minutes.')
    remove_supernatant(starting_vol-30, park=True) 

    #=======================================#
    #= Step4: Washing                      =#
    #=======================================#
    wash(wash1_vol, wash1)
    remove_supernatant(wash1_vol-30, park=True)

    wash(wash2_vol, wash2)
    remove_supernatant(wash2_vol-30, park=True)

    wash(wash3_vol, wash3)
    remove_supernatant(wash3_vol-30, park=True)

    wash(wash4_vol, wash4)
    remove_supernatant(wash4_vol+50, park=True)

    #=======================================#
    #= Step5: Elution                      =#
    #=======================================#
    if include_dry:
        ctx.delay(minutes=settling_time, msg='Incubating on MagDeck for \
' + str(settling_time) + ' minutes.')

    elute(elution_vol)

    """# track final used tip
    final_tip_tracker(ctx, tip_track=True, tip_log=tip_log)
    """

