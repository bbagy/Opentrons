from opentrons import protocol_api
from opentrons import types

metadata = {
    'protocolName': 'IDT xGEN EZ No Thermo',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.9'
    }

# SCRIPT SETTINGS
DRYRUN      = 'YES'          # YES or NO, DRYRUN = 'YES' will return tips, skip incubation times, shorten mix, for testing purposes
TIPREUSE    = 'NO'          # YES or NO, Reuses tips during Washes
NORMALASE   = 'NO'          # YES or NO, Indicates if using NORMALASE Primers

# PROTOCOL SETTINGS
COLUMNS     = 3             # 1-3
FRAGTIME    = 30            # Minutes, Duration of the Fragmentation Step
PCRCYCLES   = 4             # Amount of Cycles

# PROTOCOL BLOCKS
STEP_FRERAT         = 1
STEP_FRERATDECK     = 0
STEP_LIG            = 1
STEP_LIGDECK        = 0
STEP_POSTLIG        = 1
STEP_POSTLIGSS      = 1
STEP_PCR            = 1
STEP_PCRDECK        = 0
STEP_POSTPCR        = 1
STEP_POSTPCRSS      = 0

#STEPS = {STEP_FRERAT,STEP_LIG,STEP_POSTLIG,STEP_PCR,STEP_POSTPCR,STEP_POSTPCRSS}

p20_tips  = 0
p300_tips = 0

def run(protocol: protocol_api.ProtocolContext):
    global TIPREUSE
    global DRYRUN
    global p20_tips
    global p300_tips

    protocol.comment('THIS IS A DRY RUN') if DRYRUN == 'YES' else protocol.comment('THIS IS A REACTION RUN')

    # DECK SETUP AND LABWARE
    protocol.comment('THIS IS A MODULE RUN')
    mag_block           = protocol.load_module('magnetic module gen2','1')
    sample_plate_mag    = mag_block.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    reservoir           = protocol.load_labware('nest_12_reservoir_15ml','2')
    temp_block          = protocol.load_module('temperature module gen2', '9')
    reagent_plate       = temp_block.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul')
    tiprack_20          = protocol.load_labware('opentrons_96_filtertiprack_20ul',  '4')
    tiprack_200_1       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '5')
    tiprack_200_2       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '6')
    sample_plate_thermo = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt','3')
    tiprack_200_3       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '7')
    tiprack_200_4       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '8')
    tiprack_200_5       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '10')
    tiprack_200_6       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '11')
    if TIPREUSE == 'YES':
        protocol.comment("THIS PROTOCOL WILL REUSE TIPS FOR WASHES")

    # REAGENT PLATE
    FRERAT              = reagent_plate.wells_by_name()['A1']
    LIG                 = reagent_plate.wells_by_name()['A2']
    #/ NO PRIMER
    PCR                 = reagent_plate.wells_by_name()['A4']
    Barcodes1           = reagent_plate.wells_by_name()['A7']
    Barcodes2           = reagent_plate.wells_by_name()['A8']
    Barcodes3           = reagent_plate.wells_by_name()['A9']

    # RESERVOIR
    AMPure              = reservoir['A1']
    EtOH                = reservoir['A4']
    RSB                 = reservoir['A6']
    Liquid_trash        = reservoir['A11']

    # pipette
    p300    = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack_200_1,tiprack_200_2,tiprack_200_3,tiprack_200_4,tiprack_200_5,tiprack_200_6])
    p20     = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tiprack_20])

    #tip and sample tracking
    column_1_list = []
    column_2_list = []
    column_3_list = []
    column_4_list = []
    barcodes = []
    if COLUMNS >= 1:
        column_1_list.append('A1')
        column_2_list.append('A4')
        column_3_list.append('A7')
        column_4_list.append('A10')
        barcodes.append('A7')
    if COLUMNS >= 2:
        column_1_list.append('A2')
        column_2_list.append('A5')
        column_3_list.append('A8')
        column_4_list.append('A11')
        barcodes.append('A8')
    if COLUMNS >= 3:
        column_1_list.append('A3')
        column_2_list.append('A6')
        column_3_list.append('A9')
        column_4_list.append('A12')
        barcodes.append('A9')

    bypass = protocol.deck.position_for('11').move(types.Point(x=70,y=80,z=130))

    def p300_pick_up_tip():
        global p300_tips
        if p300_tips >= 6*12: 
            protocol.pause('RESET p300 TIPS')
            p300.reset_tipracks()
            p300_tips = 0 
        p300.pick_up_tip()
        p300_tips += 1

    def p20_pick_up_tip():
        global p20_tips
        if p20_tips >= 12:
            protocol.pause('RESET p20 TIPS')
            p20.reset_tipracks()
            p20_tips = 0
        p20.pick_up_tip()
        p20_tips += 1

    def p20_reuse_tip(loop):
        global TIPREUSE
        if TIPREUSE == 'NO':
            if p20_tips >= 12: 
                protocol.pause('RESET p20 TIPS')
                p20.reset_tipracks()
                p20_tips = 0
            p20.pick_up_tip()
        if TIPREUSE == 'YES':
            if p20_tips <=11:
                p20.pick_up_tip(tiprack_20.wells()[(p20_tips-COLUMNS+loop)*8])

    def p20_drop_tip(loop):
        global TIPREUSE
        global DRYRUN
        if DRYRUN == 'NO':
            if TIPREUSE == 'YES':
                p20.return_tip()
            else:
                p20.drop_tip()
        else:
                p20.return_tip()

    def p300_reuse_tip(loop):
        global TIPREUSE
        global p300_tips
        if TIPREUSE == 'NO':
            if p300_tips >= 12*6: 
                protocol.pause('RESET p300 TIPS')
                p300.reset_tipracks()
                p300_tips = 0
            p300.pick_up_tip()
            p300_tips += 1
        if TIPREUSE == 'YES':
            protocol.comment(str(p300_tips)+' - '+str(COLUMNS)+' + '+str(loop))
            if (p300_tips-COLUMNS+loop) <=11:
                p300.pick_up_tip(tiprack_200_1.wells()[(p300_tips-COLUMNS+loop)*8])
                protocol.comment('tiprack_200_1 : '+str((p300_tips-COLUMNS+loop)*8))
            elif (p300_tips-COLUMNS+loop) <=23:
                p300.pick_up_tip(tiprack_200_2.wells()[(p300_tips-12-COLUMNS+loop)*8])
                protocol.comment('tiprack_200_2 : '+str((p300_tips-12-COLUMNS+loop)*8))
            elif (p300_tips-COLUMNS+loop) <=35:
                p300.pick_up_tip(tiprack_200_3.wells()[(p300_tips-24-COLUMNS+loop)*8])
                protocol.comment('tiprack_200_3 : '+str((p300_tips-24-COLUMNS+loop)*8))
            elif (p300_tips-COLUMNS+loop) <=47:
                p300.pick_up_tip(tiprack_200_3.wells()[(p300_tips-36-COLUMNS+loop)*8])
                protocol.comment('tiprack_200_4 : '+str((p300_tips-36-COLUMNS+loop)*8))
            elif (p300_tips-COLUMNS+loop) <=59:
                p300.pick_up_tip(tiprack_200_3.wells()[(p300_tips-48-COLUMNS+loop)*8])
                protocol.comment('tiprack_200_5 : '+str((p300_tips-48-COLUMNS+loop)*8))
            elif (p300_tips-COLUMNS+loop) <=71:
                p300.pick_up_tip(tiprack_200_3.wells()[(p300_tips-60-COLUMNS+loop)*8])
                protocol.comment('tiprack_200_6 : '+str((p300_tips-60-COLUMNS+loop)*8))

    def p300_drop_tip(loop):
        global TIPREUSE
        global DRYRUN
        if DRYRUN == 'NO':
            if TIPREUSE == 'YES':
                p300.return_tip()
            else:
                p300.drop_tip()
        else:
                p300.return_tip()

    def p300_move_to(well,pos):
        if well in ('A1','A3','A5','A7','A9','A11'):
            if pos == 'p300_bead_side':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=-0.50,y=0,z=-7.2)))
            if pos == 'p300_bead_top':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=1.30,y=0,z=-1)))
            if pos == 'p300_bead_mid':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=0.80,y=0,z=-4)))
            if pos == 'p300_loc1':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=1.3*0.8,y=1.3*0.8,z=-4)))
            if pos == 'p300_loc2':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=1.3,y=0,z=-4)))
            if pos == 'p300_loc3':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=1.3,y=0,z=-4)))
        if well in ('A2','A4','A6','A8','A10','A12'):
            if pos == 'p300_bead_side':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=0.50,y=0,z=-7.2)))
            if pos == 'p300_bead_top':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=-1.30,y=0,z=-1)))
            if pos == 'p300_bead_mid':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=-0.80,y=0,z=-4)))
            if pos == 'p300_loc1':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=-1.3*0.8,y=1.3*0.8,z=-4)))
            if pos == 'p300_loc2':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=-1.3,y=0,z=-4)))
            if pos == 'p300_loc3':
                p300.move_to(sample_plate_mag[X].center().move(types.Point(x=-1.3,y=0,z=-4)))

    def p20_move_to(well,pos):
        if well in ('A1','A3','A5','A7','A9','A11'):
            if pos == 'p20_bead_side':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=-0.50,y=0,z=-7.2)))
            if pos == 'p20_bead_top':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=1.30,y=0,z=-1)))
            if pos == 'p20_bead_mid':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=0.80,y=0,z=-4)))
            if pos == 'p20_loc1':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=1.3*0.8,y=1.3*0.8,z=-4)))
            if pos == 'p20_loc2':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=1.3,y=0,z=-4)))
            if pos == 'p20_loc3':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=1.3,y=0,z=-4)))
        if well in ('A2','A4','A6','A8','A10','A12'):
            if pos == 'p20_bead_side':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=0.50,y=0,z=-7.2)))
            if pos == 'p20_bead_top':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=-1.30,y=0,z=-1)))
            if pos == 'p20_bead_mid':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=-0.80,y=0,z=-4)))
            if pos == 'p20_loc1':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=-1.3*0.8,y=1.3*0.8,z=-4)))
            if pos == 'p20_loc2':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=-1.3,y=0,z=-4)))
            if pos == 'p20_loc3':
                p20.move_to(sample_plate_mag[X].center().move(types.Point(x=-1.3,y=0,z=-4)))
    
    # commands
    if DRYRUN == 'NO':
        protocol.comment("SETTING THERMO and TEMP BLOCK Temperature")
#        thermocycler.set_block_temperature(4)
#        thermocycler.set_lid_temperature(70)    
        temp_block.set_temperature(4)
#        thermocycler.open_lid()
        protocol.pause("Ready")

    if STEP_FRERAT == 1:
        protocol.comment('==============================================')
        protocol.comment('--> Fragmenting / End Repair / A-Tailing')
        protocol.comment('==============================================')

        protocol.comment('--> Adding FRERAT')
        FRERATVol    = 10.5
        FRERATMixRep = 10 if DRYRUN == 'NO' else 1
        FRERATMixVol = 20
        for loop, X in enumerate(column_1_list):
            p20_pick_up_tip()
            p20.aspirate(FRERATVol, FRERAT.bottom())
            p20.dispense(FRERATVol, sample_plate_thermo.wells_by_name()[X].bottom())
            p20.move_to(sample_plate_thermo[X].bottom())
            p20.mix(FRERATMixRep,FRERATMixVol)
            p20.drop_tip() if DRYRUN == 'NO' else p20.return_tip()

    if STEP_FRERATDECK == 1:
        if DRYRUN == 'NO':
            ############################################################################################################################################
            protocol.pause('Seal, Run FRERAT (60min)')

            thermocycler.close_lid()
            profile_FRERAT = [
                {'temperature': 32, 'hold_time_minutes': FRAGTIME},
                {'temperature': 65, 'hold_time_minutes': 30}
                ]
            thermocycler.execute_profile(steps=profile_FRERAT, repetitions=1, block_max_volume=50)
            thermocycler.set_block_temperature(4)
            ############################################################################################################################################
            thermocycler.open_lid()
            protocol.pause("Remove Seal")
    else:
        protocol.pause('Seal, Run FRERAT (60min)')

    if STEP_LIG == 1:
        protocol.comment('==============================================')
        protocol.comment('--> Adapter Ligation')
        protocol.comment('==============================================')

        protocol.comment('--> Adding Lig')
        LIGVol = 30
        LIGMixRep = 40 if DRYRUN == 'NO' else 1
        LIGMixVol = 55
        for loop, X in enumerate(column_1_list):
            p300_pick_up_tip()
            p300.mix(3,LIGVol, LIG.bottom(z=1), rate=0.5)
            p300.aspirate(LIGVol, LIG.bottom(z=1), rate=0.2)
            p300.default_speed = 5
            p300.move_to(LIG.top(5))
            protocol.delay(seconds=0.2)
            p300.default_speed = 400
            p300.dispense(LIGVol, sample_plate_thermo[X].bottom(), rate=0.25)
            p300.move_to(sample_plate_thermo[X].bottom())
            p300.mix(LIGMixRep,LIGMixVol, rate=0.5)
            p300.blow_out(sample_plate_thermo[X].top(z=-5))
            p300.move_to(bypass) 
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

    if STEP_LIGDECK == 1:
        if DRYRUN == 'NO':
            ############################################################################################################################################
            protocol.pause('Seal, Run LIG (15min)')

            profile_LIG = [
                {'temperature': 20, 'hold_time_minutes': 20}
                ]
            thermocycler.execute_profile(steps=profile_LIG, repetitions=1, block_max_volume=50)
            thermocycler.set_block_temperature(4)
            ############################################################################################################################################
            thermocycler.open_lid()
            protocol.pause("Remove Seal")
    else:
        protocol.pause('Seal, Run LIG (20min)')

    if STEP_POSTLIG == 1:
        protocol.comment('==============================================')
        protocol.comment('--> Cleanup 1')
        protocol.comment('==============================================')
            
        if DRYRUN == 'NO':
            protocol.pause('PLACE sample_plate_mag MAGNET')

        protocol.comment('--> ADDING AMPure (0.8x)')
        AMPureVol = 48
        AMPureMixRep = 40 if DRYRUN == 'NO' else 1
        AMPureMixVol = 90
        AMPurePremix = 10 if DRYRUN == 'NO' else 1
        for loop, X in enumerate(column_1_list):
            p300_pick_up_tip()
            p300.mix(AMPurePremix,AMPureVol+10, AMPure.bottom())
            p300.aspirate(AMPureVol, AMPure.bottom(), rate=0.25)
            p300.dispense(AMPureVol/2, sample_plate_mag[X].bottom(), rate=0.25)
            p300.default_speed = 5
            p300.dispense(AMPureVol/2, sample_plate_mag[X].center(), rate=0.25)
            p300.move_to(sample_plate_mag[X].center())
            for Mix in range(AMPureMixRep):
                p300.aspirate(AMPureMixVol/2, rate=0.5)
                p300.move_to(sample_plate_mag[X].bottom())
                p300.aspirate(AMPureMixVol/2, rate=0.5)
                p300.dispense(AMPureMixVol/2, rate=0.5)
                p300.move_to(sample_plate_mag[X].center())
                p300.dispense(AMPureMixVol/2, rate=0.5)
                Mix += 1
            p300.blow_out(sample_plate_mag[X].top(z=1))
            p300.default_speed = 400
            p300.move_to(bypass)              
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            if COLUMNS == 1:
                protocol.delay(minutes=4.2)
            if COLUMNS == 2:
                protocol.delay(minutes=2.5)
            if COLUMNS == 3:
                protocol.delay(minutes=1)

            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=8.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=6)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=1)

        protocol.comment('--> Removing Supernatant')
        RemoveSup = 200
        for loop, X in enumerate(column_1_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(z=4))
            p300.aspirate(RemoveSup-20, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.2)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #1')
        ETOHMaxVol = 150
        for loop, X in enumerate(column_1_list):
            p300_pick_up_tip()
            p300.aspirate(ETOHMaxVol, EtOH.bottom())
            p300_move_to(X,'p300_bead_side')
            p300.dispense(ETOHMaxVol-50, rate=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.dispense(50, rate=0.5)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 5
            p300.move_to(sample_plate_mag[X].top(z=-2))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.default_speed = 400
            p300_drop_tip(loop)

        protocol.delay(minutes=0.5)
        
        protocol.comment('--> Remove ETOH Wash #1')
        for loop, X in enumerate(column_1_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(4))
            p300.aspirate(ETOHMaxVol, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(200-ETOHMaxVol, rate=0.25)
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #2')
        ETOHMaxVol = 150
        for loop, X in enumerate(column_1_list):
            p300_pick_up_tip()
            p300.aspirate(ETOHMaxVol, EtOH.bottom())
            p300_move_to(X,'p300_bead_side')
            p300.dispense(ETOHMaxVol-50, rate=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.dispense(50, rate=0.5)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 5
            p300.move_to(sample_plate_mag[X].top(z=-2))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.default_speed = 400
            p300_drop_tip(loop)

        protocol.delay(minutes=0.5)
        
        protocol.comment('--> Remove ETOH Wash #2')
        for loop, X in enumerate(column_1_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(4))
            p300.aspirate(ETOHMaxVol, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(200-ETOHMaxVol, rate=0.25)
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            protocol.delay(minutes=2)

        protocol.comment('--> Removing Residual ETOH')
        for loop, X in enumerate(column_1_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(1))
            p300.aspirate(20, rate=0.25)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            mag_block.engage(height_from_base=6)
            protocol.comment('AIR DRY')
            protocol.delay(minutes=0.5)

            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

        protocol.comment('--> Adding RSB')
        RSBVol = 21 if STEP_POSTLIGSS == 0 else 52
        RSBMixRep = 5 if DRYRUN == 'NO' else 1
        RSBMixVol = 20 if STEP_POSTLIGSS == 0 else 50
        for loop, X in enumerate(column_1_list):
            p300_pick_up_tip()
            p300.aspirate(RSBVol, RSB.bottom())
            p300_move_to(X,'p300_loc1')
            p300.dispense(RSBVol/5, rate=0.75)
            p300.default_speed = 5
            p300_move_to(X,'p300_loc2')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc3')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc2')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc1')
            p300.dispense(RSBVol/5, rate=0.75)
            reps = 5
            for x in range(reps):
                p300.move_to(sample_plate_mag[X].bottom())
                p300.aspirate(RSBVol, rate=0.5)
                p300_move_to(X,'p300_bead_top')
                p300.dispense(RSBVol, rate=1)
            reps = 3
            for x in range(reps):    
                p300_move_to(X,'p300_loc2')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc1')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc2')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc3')
                p300.mix(RSBMixRep,RSBMixVol)
            p300.move_to(sample_plate_mag.wells_by_name()[X].bottom())
            p300.mix(RSBMixRep,RSBMixVol)
            p300.move_to(sample_plate_mag.wells_by_name()[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag.wells_by_name()[X].center())
            p300.default_speed = 400
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=4)

        protocol.comment('--> Transferring Supernatant')
        TransferSup = 20 if STEP_POSTLIGSS == 0 else 50
        for loop, X in enumerate(column_1_list):
            Y = 'A5'
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom())
            p300.aspirate(TransferSup, rate=0.25)
            if STEP_POSTLIGSS == 0:
                p300.dispense(TransferSup+5, sample_plate_mag[column_2_list[loop]].bottom())
            else:
                p300.dispense(TransferSup+5, sample_plate_mag[column_4_list[loop]].bottom())
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

    if STEP_POSTLIGSS == 1:
        protocol.comment('==============================================')
        protocol.comment('--> Size Selection')
        protocol.comment('==============================================')
            
        if DRYRUN == 'NO':
            protocol.pause('PLACE sample_plate_mag MAGNET')

        protocol.comment('--> ADDING AMPure (0.65x)')
        AMPureVol = 32.5
        AMPureMixRep = 50 if DRYRUN == 'NO' else 1
        AMPureMixVol = 80
        AMPurePremix = 10 if DRYRUN == 'NO' else 1
        for loop, X in enumerate(column_4_list):
            p300_pick_up_tip()
            p300.mix(AMPurePremix,AMPureVol+10, AMPure.bottom())
            p300.aspirate(AMPureVol, AMPure.bottom(), rate=0.25)
            p300.dispense(AMPureVol/2, sample_plate_mag[X].bottom(), rate=0.25)
            p300.default_speed = 5
            p300.dispense(AMPureVol/2, sample_plate_mag[X].center(), rate=0.25)
            p300.move_to(sample_plate_mag[X].center())
            for Mix in range(AMPureMixRep):
                p300.aspirate(AMPureMixVol/2, rate=0.5)
                p300.move_to(sample_plate_mag[X].bottom())
                p300.aspirate(AMPureMixVol/2, rate=0.5)
                p300.dispense(AMPureMixVol/2, rate=0.5)
                p300.move_to(sample_plate_mag[X].center())
                p300.dispense(AMPureMixVol/2, rate=0.5)
                Mix += 1
            p300.blow_out(sample_plate_mag[X].top(z=1))
            p300.default_speed = 400
            p300.move_to(bypass)              
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            if COLUMNS == 1:
                protocol.delay(minutes=4.2)
            if COLUMNS == 2:
                protocol.delay(minutes=2.5)
            if COLUMNS == 3:
                protocol.delay(minutes=1)

            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=8.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=6)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=1)

        protocol.comment('--> Removing Supernatant')
        RemoveSup = 200
        for loop, X in enumerate(column_4_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(z=4))
            p300.aspirate(RemoveSup-20, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.2)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #1')
        ETOHMaxVol = 150
        for loop, X in enumerate(column_4_list):
            p300_pick_up_tip()
            p300.aspirate(ETOHMaxVol, EtOH.bottom())
            p300_move_to(X,'p300_bead_side')
            p300.dispense(ETOHMaxVol-50, rate=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.dispense(50, rate=0.5)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 5
            p300.move_to(sample_plate_mag[X].top(z=-2))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.default_speed = 400
            p300_drop_tip(loop)

        protocol.delay(minutes=0.5)
        
        protocol.comment('--> Remove ETOH Wash #1')
        for loop, X in enumerate(column_4_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(4))
            p300.aspirate(ETOHMaxVol, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(200-ETOHMaxVol, rate=0.25)
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #2')
        ETOHMaxVol = 150
        for loop, X in enumerate(column_4_list):
            p300_pick_up_tip()
            p300.aspirate(ETOHMaxVol, EtOH.bottom())
            p300_move_to(X,'p300_bead_side')
            p300.dispense(ETOHMaxVol-50, rate=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.dispense(50, rate=0.5)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 5
            p300.move_to(sample_plate_mag[X].top(z=-2))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.default_speed = 400
            p300_drop_tip(loop)

        protocol.delay(minutes=0.5)
        
        protocol.comment('--> Remove ETOH Wash #2')
        for loop, X in enumerate(column_4_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(4))
            p300.aspirate(ETOHMaxVol, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(200-ETOHMaxVol, rate=0.25)
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            protocol.delay(minutes=2)

        protocol.comment('--> Removing Residual ETOH')
        for loop, X in enumerate(column_4_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(1))
            p300.aspirate(20, rate=0.25)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            mag_block.engage(height_from_base=6)
            protocol.comment('AIR DRY')
            protocol.delay(minutes=0.5)

            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

        protocol.comment('--> Adding RSB')
        RSBVol = 21
        RSBMixRep = 5 if DRYRUN == 'NO' else 1
        RSBMixVol = 20
        for loop, X in enumerate(column_4_list):
            p300_pick_up_tip()
            p300.aspirate(RSBVol, RSB.bottom())
            p300_move_to(X,'p300_loc1')
            p300.dispense(RSBVol/5, rate=0.75)
            p300.default_speed = 5
            p300_move_to(X,'p300_loc2')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc3')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc2')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc1')
            p300.dispense(RSBVol/5, rate=0.75)
            reps = 5
            for x in range(reps):
                p300.move_to(sample_plate_mag[X].bottom())
                p300.aspirate(RSBVol, rate=0.5)
                p300_move_to(X,'p300_bead_top')
                p300.dispense(RSBVol, rate=1)
            reps = 3
            for x in range(reps):    
                p300_move_to(X,'p300_loc2')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc1')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc2')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc3')
                p300.mix(RSBMixRep,RSBMixVol)
            p300.move_to(sample_plate_mag.wells_by_name()[X].bottom())
            p300.mix(RSBMixRep,RSBMixVol)
            p300.move_to(sample_plate_mag.wells_by_name()[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag.wells_by_name()[X].center())
            p300.default_speed = 400
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=4)

        protocol.comment('--> Transferring Supernatant')
        TransferSup = 20
        for loop, X in enumerate(column_4_list):
            Y = 'A5'
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom())
            p300.aspirate(TransferSup, rate=0.25)
            p300.dispense(TransferSup+5, sample_plate_mag[column_2_list[loop]].bottom())
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

    if STEP_PCR == 1:
        protocol.comment('==============================================')
        protocol.comment('--> Amplification')
        protocol.comment('==============================================')

        if NORMALASE == 'YES':
            protocol.comment('--> Adding Barcodes and R7')
        else:
            protocol.comment('--> Adding Barcodes')
        BarcodeVol    = 5
        BarcodeMixRep = 3 if DRYRUN == 'NO' else 1
        BarcodeMixVol = 10
        for loop, X in enumerate(column_2_list):
            p20_pick_up_tip()
            p20.aspirate(BarcodeVol, reagent_plate.wells_by_name()[barcodes[loop]].bottom(), rate=0.25)
            p20.dispense(BarcodeVol, sample_plate_mag.wells_by_name()[X].bottom(1))
            p20.mix(BarcodeMixRep,BarcodeMixVol)
            p20_drop_tip(loop)

        protocol.comment('--> Adding PCR')
        PCRVol    = 25
        PCRMixRep = 10 if DRYRUN == 'NO' else 1
        PCRMixVol = 50
        for loop, X in enumerate(column_2_list):
            p300_pick_up_tip()
            p300.mix(2,PCRVol, PCR.bottom(), rate=0.5)
            p300.aspirate(PCRVol, PCR.bottom(), rate=0.25)
            p300.dispense(PCRVol, sample_plate_mag[X].bottom(), rate=0.25)
            p300.mix(PCRMixRep, PCRMixVol, rate=0.5)
            p300.move_to(sample_plate_mag[X].bottom())
            protocol.delay(minutes=0.1)
            p300.blow_out(sample_plate_mag[X].top(z=-5))
            p300.move_to(bypass)
            p300_drop_tip(loop)

    if STEP_PCRDECK == 1:
        if DRYRUN == 'NO':

            ############################################################################################################################################
            protocol.pause('Seal, Run PCR (60min)')
            thermocycler.set_lid_temperature(105)
            thermocycler.close_lid()
            profile_PCR_1 = [
                {'temperature': 98, 'hold_time_seconds': 45}
                ]
            thermocycler.execute_profile(steps=profile_PCR_1, repetitions=1, block_max_volume=50)
            profile_PCR_2 = [
                {'temperature': 98, 'hold_time_seconds': 15},
                {'temperature': 60, 'hold_time_seconds': 30},
                {'temperature': 72, 'hold_time_seconds': 30}
                ]
            thermocycler.execute_profile(steps=profile_PCR_2, repetitions=PCRCYCLES, block_max_volume=50)
            profile_PCR_3 = [
                {'temperature': 72, 'hold_time_minutes': 1}
                ]
            thermocycler.execute_profile(steps=profile_PCR_3, repetitions=1, block_max_volume=50)
            thermocycler.set_block_temperature(4)
            ############################################################################################################################################
            thermocycler.open_lid()
            protocol.pause("Remove Seal")
            protocol.pause("PLACE sample_plate_mag MAGNET")
    else:
        protocol.pause('Seal, Run PCR (60min)')

    Liquid_trash        = reservoir['A11']

    if STEP_POSTPCR == 1:
        protocol.comment('==============================================')
        protocol.comment('--> Cleanup 2')
        protocol.comment('==============================================')
            
        if DRYRUN == 'NO':
            protocol.pause('PLACE sample_plate_mag MAGNET')

        protocol.comment('--> ADDING AMPure (0.65x)')
        AMPureVol = 32.5
        AMPureMixRep = 50 if DRYRUN == 'NO' else 1
        AMPureMixVol = 80
        AMPurePremix = 10 if DRYRUN == 'NO' else 1
        for loop, X in enumerate(column_2_list):
            p300_pick_up_tip()
            p300.mix(AMPurePremix,AMPureVol+10, AMPure.bottom())
            p300.aspirate(AMPureVol, AMPure.bottom(), rate=0.25)
            p300.dispense(AMPureVol/2, sample_plate_mag[X].bottom(), rate=0.25)
            p300.default_speed = 5
            p300.dispense(AMPureVol/2, sample_plate_mag[X].center(), rate=0.25)
            p300.move_to(sample_plate_mag[X].center())
            for Mix in range(AMPureMixRep):
                p300.aspirate(AMPureMixVol/2, rate=0.5)
                p300.move_to(sample_plate_mag[X].bottom())
                p300.aspirate(AMPureMixVol/2, rate=0.5)
                p300.dispense(AMPureMixVol/2, rate=0.5)
                p300.move_to(sample_plate_mag[X].center())
                p300.dispense(AMPureMixVol/2, rate=0.5)
                Mix += 1
            p300.blow_out(sample_plate_mag[X].top(z=1))
            p300.default_speed = 400
            p300.move_to(bypass)              
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            if COLUMNS == 1:
                protocol.delay(minutes=4.2)
            if COLUMNS == 2:
                protocol.delay(minutes=2.5)
            if COLUMNS >= 3:
                protocol.delay(minutes=1)

            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=8.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=6)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=1)

        protocol.comment('--> Removing Supernatant')
        RemoveSup = 200
        for loop, X in enumerate(column_2_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(z=4))
            p300.aspirate(RemoveSup-20, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.2)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #1')
        ETOHMaxVol = 150
        for loop, X in enumerate(column_2_list):
            p300_pick_up_tip()
            p300.aspirate(ETOHMaxVol, EtOH.bottom())
            p300_move_to(X,'p300_bead_side')
            p300.dispense(ETOHMaxVol-50, rate=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.dispense(50, rate=0.5)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 5
            p300.move_to(sample_plate_mag[X].top(z=-2))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.default_speed = 400
            p300_drop_tip(loop)

        protocol.delay(minutes=0.5)
        
        protocol.comment('--> Remove ETOH Wash #1')
        for loop, X in enumerate(column_2_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(4))
            p300.aspirate(ETOHMaxVol, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(200-ETOHMaxVol, rate=0.25)
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #2')
        ETOHMaxVol = 150
        for loop, X in enumerate(column_2_list):
            p300_pick_up_tip()
            p300.aspirate(ETOHMaxVol, EtOH.bottom())
            p300_move_to(X,'p300_bead_side')
            p300.dispense(ETOHMaxVol-50, rate=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.dispense(50, rate=0.5)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 5
            p300.move_to(sample_plate_mag[X].top(z=-2))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.default_speed = 400
            p300_drop_tip(loop)

        protocol.delay(minutes=0.5)
        
        protocol.comment('--> Remove ETOH Wash #2')
        for loop, X in enumerate(column_2_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(4))
            p300.aspirate(ETOHMaxVol, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(200-ETOHMaxVol, rate=0.25)
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            protocol.delay(minutes=2)

        protocol.comment('--> Removing Residual ETOH')
        for loop, X in enumerate(column_2_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(1))
            p300.aspirate(20, rate=0.25)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            mag_block.engage(height_from_base=6)
            protocol.comment('AIR DRY')
            protocol.delay(minutes=0.5)

            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

        protocol.comment('--> Adding RSB')
        RSBVol = 25
        RSBMixRep = 5 if DRYRUN == 'NO' else 1
        RSBMixVol = 20
        for loop, X in enumerate(column_2_list):
            p300_pick_up_tip()
            p300.aspirate(RSBVol, RSB.bottom())
            p300_move_to(X,'p300_loc1')
            p300.dispense(RSBVol/5, rate=0.75)
            p300.default_speed = 5
            p300_move_to(X,'p300_loc2')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc3')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc2')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc1')
            p300.dispense(RSBVol/5, rate=0.75)
            reps = 5
            for x in range(reps):
                p300.move_to(sample_plate_mag[X].bottom())
                p300.aspirate(RSBVol, rate=0.5)
                p300_move_to(X,'p300_bead_top')
                p300.dispense(RSBVol, rate=1)
            reps = 3
            for x in range(reps):    
                p300_move_to(X,'p300_loc2')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc1')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc2')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc3')
                p300.mix(RSBMixRep,RSBMixVol)
            p300.move_to(sample_plate_mag.wells_by_name()[X].bottom())
            p300.mix(RSBMixRep,RSBMixVol)
            p300.move_to(sample_plate_mag.wells_by_name()[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag.wells_by_name()[X].center())
            p300.default_speed = 400
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=4)

        protocol.comment('--> Transferring Supernatant')
        TransferSup = 20
        for loop, X in enumerate(column_2_list):
            Y = 'A5'
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom())
            p300.aspirate(TransferSup, rate=0.25)
            p300.dispense(TransferSup+5, sample_plate_mag[column_3_list[loop]].bottom())
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

    if STEP_POSTPCRSS == 1:
        protocol.comment('==============================================')
        protocol.comment('--> Cleanup 3')
        protocol.comment('==============================================')

        protocol.comment('--> ADDING AMPure (0.65x)')
        AMPureVol = 24
        AMPureMixRep = 50 if DRYRUN == 'NO' else 1
        AMPureMixVol = 80
        AMPurePremix = 10 if DRYRUN == 'NO' else 1
        for loop, X in enumerate(column_3_list):
            p300_pick_up_tip()
            p300.mix(AMPurePremix,AMPureVol+10, AMPure.bottom())
            p300.aspirate(AMPureVol, AMPure.bottom(), rate=0.25)
            p300.dispense(AMPureVol/2, sample_plate_mag[X].bottom(), rate=0.25)
            p300.default_speed = 5
            p300.dispense(AMPureVol/2, sample_plate_mag[X].center(), rate=0.25)
            p300.move_to(sample_plate_mag[X].center())
            for Mix in range(AMPureMixRep):
                p300.aspirate(AMPureMixVol/2, rate=0.5)
                p300.move_to(sample_plate_mag[X].bottom())
                p300.aspirate(AMPureMixVol/2, rate=0.5)
                p300.dispense(AMPureMixVol/2, rate=0.5)
                p300.move_to(sample_plate_mag[X].center())
                p300.dispense(AMPureMixVol/2, rate=0.5)
                Mix += 1
            p300.blow_out(sample_plate_mag[X].top(z=1))
            p300.default_speed = 400
            p300.move_to(bypass)              
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            if COLUMNS == 1:
                protocol.delay(minutes=4.2)
            if COLUMNS == 2:
                protocol.delay(minutes=2.5)
            if COLUMNS >= 3:
                protocol.delay(minutes=1)

            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=8.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7.5)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=7)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=6)
            protocol.delay(minutes=1)
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=1)

        protocol.comment('--> Removing Supernatant')
        RemoveSup = 200
        for loop, X in enumerate(column_3_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(z=4))
            p300.aspirate(RemoveSup-20, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(20, rate=0.2)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #1')
        ETOHMaxVol = 150
        for loop, X in enumerate(column_3_list):
            p300_pick_up_tip()
            p300.aspirate(ETOHMaxVol, EtOH.bottom())
            p300_move_to(X,'p300_bead_side')
            p300.dispense(ETOHMaxVol-50, rate=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.dispense(50, rate=0.5)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 5
            p300.move_to(sample_plate_mag[X].top(z=-2))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.default_speed = 400
            p300_drop_tip(loop)

        protocol.delay(minutes=0.5)
        
        protocol.comment('--> Remove ETOH Wash #1')
        for loop, X in enumerate(column_3_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(4))
            p300.aspirate(ETOHMaxVol, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(200-ETOHMaxVol, rate=0.25)
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #2')
        ETOHMaxVol = 150
        for loop, X in enumerate(column_3_list):
            p300_pick_up_tip()
            p300.aspirate(ETOHMaxVol, EtOH.bottom())
            p300_move_to(X,'p300_bead_side')
            p300.dispense(ETOHMaxVol-50, rate=0.5)
            p300.move_to(sample_plate_mag[X].center())
            p300.dispense(50, rate=0.5)
            p300.move_to(sample_plate_mag[X].top(z=2))
            p300.default_speed = 5
            p300.move_to(sample_plate_mag[X].top(z=-2))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300.default_speed = 400
            p300_drop_tip(loop)

        protocol.delay(minutes=0.5)
        
        protocol.comment('--> Remove ETOH Wash #2')
        for loop, X in enumerate(column_3_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(4))
            p300.aspirate(ETOHMaxVol, rate=0.25)
            p300.default_speed = 5
            p300_move_to(X,'p300_bead_side')
            protocol.delay(minutes=0.1)
            p300.aspirate(200-ETOHMaxVol, rate=0.25)
            p300.default_speed = 400
            p300.dispense(200, Liquid_trash)
            p300.move_to(Liquid_trash.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            protocol.delay(minutes=2)

        protocol.comment('--> Removing Residual ETOH')
        for loop, X in enumerate(column_3_list):
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom(1))
            p300.aspirate(20, rate=0.25)
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            mag_block.engage(height_from_base=6)
            protocol.comment('AIR DRY')
            protocol.delay(minutes=0.5)

            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()

        protocol.comment('--> Adding RSB')
        RSBVol = 25
        RSBMixRep = 5 if DRYRUN == 'NO' else 1
        RSBMixVol = 20
        for loop, X in enumerate(column_3_list):
            p300_pick_up_tip()
            p300.aspirate(RSBVol, RSB.bottom())
            p300_move_to(X,'p300_loc1')
            p300.dispense(RSBVol/5, rate=0.75)
            p300.default_speed = 5
            p300_move_to(X,'p300_loc2')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc3')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc2')
            p300.dispense(RSBVol/5, rate=0.75)
            p300_move_to(X,'p300_loc1')
            p300.dispense(RSBVol/5, rate=0.75)
            reps = 5
            for x in range(reps):
                p300.move_to(sample_plate_mag[X].bottom())
                p300.aspirate(RSBVol, rate=0.5)
                p300_move_to(X,'p300_bead_top')
                p300.dispense(RSBVol, rate=1)
            reps = 3
            for x in range(reps):    
                p300_move_to(X,'p300_loc2')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc1')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc2')
                p300.mix(RSBMixRep,RSBMixVol)
                p300_move_to(X,'p300_loc3')
                p300.mix(RSBMixRep,RSBMixVol)
            p300.move_to(sample_plate_mag.wells_by_name()[X].bottom())
            p300.mix(RSBMixRep,RSBMixVol)
            p300.move_to(sample_plate_mag.wells_by_name()[X].top())
            protocol.delay(seconds=0.5)
            p300.move_to(sample_plate_mag.wells_by_name()[X].center())
            p300.default_speed = 400
            p300_drop_tip(loop)

        if DRYRUN == 'NO':
            protocol.comment('MAGNET ENGAGE')
            mag_block.engage(height_from_base=5)
            protocol.delay(minutes=4)

        protocol.comment('--> Transferring Supernatant')
        TransferSup = 20
        for loop, X in enumerate(column_3_list):
            Y = 'A5'
            p300_reuse_tip(loop)
            p300.move_to(sample_plate_mag[X].bottom())
            p300.aspirate(TransferSup, rate=0.25)
            p300.dispense(TransferSup+5, sample_plate_mag[column_4_list[loop]].bottom())
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()
