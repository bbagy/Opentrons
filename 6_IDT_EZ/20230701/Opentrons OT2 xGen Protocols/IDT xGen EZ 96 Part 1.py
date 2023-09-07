from opentrons import protocol_api
from opentrons import types

metadata = {
    'protocolName': 'IDT xGEN EZ 96 Part 1',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library',
    'apiLevel': '2.9'
    }

# SCRIPT SETTINGS
DRYRUN      = 'YES'          # YES or NO, DRYRUN = 'YES' will return tips, skip incubation times, shorten mix, for testing purposes
TIPREUSE    = 'YES'          # YES or NO, Reuses tips during Washes
NORMALASE   = 'NO'          # YES or NO, Indicates if using NORMALASE Primers

# PROTOCOL SETTINGS
COLUMNS     = 12             # 1-3
FRAGTIME    = 30            # Minutes, Duration of the Fragmentation Step
TIPMIX      = 'NO'

# PROTOCOL BLOCKS
STEP_FRERAT         = 1
STEP_LIG            = 1
STEP_POSTLIG        = 1
STEP_POSTLIGSS      = 0

p20_tips  = 0
p300_tips = 0
Liquid_trash = 0

def run(protocol: protocol_api.ProtocolContext):
    global TIPREUSE
    global DRYRUN
    global p20_tips
    global p300_tips
    global Liquid_trash
    global TIPMIX

    protocol.comment('THIS IS A DRY RUN') if DRYRUN == 'YES' else protocol.comment('THIS IS A REACTION RUN')

    # DECK SETUP AND LABWARE
    protocol.comment('THIS IS A MODULE RUN')
    mag_block           = protocol.load_module('magnetic module gen2','1')
    sample_plate_mag    = mag_block.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    reservoir           = protocol.load_labware('nest_12_reservoir_15ml','2')
    temp_block          = protocol.load_module('temperature module gen2', '3')
    reagent_plate       = temp_block.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul')
    tiprack_20          = protocol.load_labware('opentrons_96_filtertiprack_20ul',  '4')
    tiprack_200_1       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '5')
    tiprack_200_2       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '6')
    sample_plate_thermo = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt','7')
    tiprack_200_3       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '8')
    tiprack_200_4       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '9')
    sample_plate_final  = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt','10')
    tiprack_200_5       = protocol.load_labware('opentrons_96_filtertiprack_200ul', '11')

    Totalp300 = 5
    Totalp20 = 1

    if TIPREUSE == 'YES':
        protocol.comment("THIS PROTOCOL WILL REUSE TIPS FOR WASHES")

    # REAGENT PLATE
    FRERAT              = reagent_plate.wells_by_name()['A1']
    LIG_1               = reagent_plate.wells_by_name()['A2']
    LIG_2               = reagent_plate.wells_by_name()['A3']

    # RESERVOIR
    AMPure              = reservoir['A1']
    EtOH_1              = reservoir['A2']
    EtOH_2              = reservoir['A3']
    EtOH_3              = reservoir['A4']
    EtOH_4              = reservoir['A5']
    RSB                 = reservoir['A6']
    Liquid_trash_1      = reservoir['A10']
    Liquid_trash_2      = reservoir['A11']
    Liquid_trash_3      = reservoir['A12']

    # pipette
    p300    = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack_200_1,tiprack_200_2,tiprack_200_3,tiprack_200_4,tiprack_200_5])
    p20     = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tiprack_20])

    #tip and sample tracking
    column_1_list = ['A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','A11','A12']
    column_2_list = ['A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','A11','A12']

    bypass = protocol.deck.position_for('11').move(types.Point(x=70,y=80,z=130))

    def p300_pick_up_tip():
        global p300_tips
        if p300_tips >= Totalp300*12: 
            protocol.pause('RESET p300 TIPS')
            p300.reset_tipracks()
            p300_tips = 0 
        p300.pick_up_tip()
        p300_tips += 1

    def p20_pick_up_tip():
        global p20_tips
        if p20_tips >= Totalp20*12:
            protocol.pause('RESET p20 TIPS')
            p20.reset_tipracks()
            p20_tips = 0
        p20.pick_up_tip()
        p20_tips += 1

    def p20_reuse_tip(loop):
        global TIPREUSE
        if TIPREUSE == 'NO':
            if p20_tips >= Totalp20*12: 
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
            if p300_tips >= 12*Totalp300: 
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

    def p300_dispose(disposevol):
        global Liquid_trash
        if Liquid_trash <= 1400:
            p300.dispense(disposevol, Liquid_trash_1)
            p300.move_to(Liquid_trash_1.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            Liquid_trash += disposevol
        elif Liquid_trash <= 2800:
            p300.dispense(disposevol, Liquid_trash_2)
            p300.move_to(Liquid_trash_2.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            Liquid_trash += disposevol
        elif Liquid_trash > 2800:
            p300.dispense(disposevol, Liquid_trash_3)
            p300.move_to(Liquid_trash_3.top(z=5))
            protocol.delay(minutes=0.1)
            p300.blow_out()
            Liquid_trash += disposevol

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
        temp_block.set_temperature(4)
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

    protocol.pause('Seal, Run ERAT (60min)')

    if STEP_LIG == 1:
        protocol.comment('==============================================')
        protocol.comment('--> Adapter Ligation')
        protocol.comment('==============================================')

        protocol.comment('--> Adding Lig')
        LIGVol = 30
        LIGMixRep = 40 if DRYRUN == 'NO' else 1
        LIGMixVol = 55
        LIGCOUNT = 0
        for loop, X in enumerate(column_1_list):
            p300_pick_up_tip()
            if LIGCOUNT <= 5:
                p300.mix(3,LIGVol, LIG_1.bottom(z=1), rate=0.5)
                p300.aspirate(LIGVol, LIG_1.bottom(z=1), rate=0.2)
                p300.default_speed = 5
                p300.move_to(LIG_1.top(5))
            else:
                p300.mix(3,LIGVol, LIG_2.bottom(z=1), rate=0.5)
                p300.aspirate(LIGVol, LIG_2.bottom(z=1), rate=0.2)
                p300.default_speed = 5
                p300.move_to(LIG_2.top(5))
            LIGCOUNT += 1
            protocol.delay(seconds=0.2)
            p300.default_speed = 400
            p300.dispense(LIGVol, sample_plate_thermo[X].bottom(), rate=0.25)
            p300.move_to(sample_plate_thermo[X].bottom())
            p300.mix(LIGMixRep,LIGMixVol, rate=0.5)
            p300.blow_out(sample_plate_thermo[X].top(z=-5))
            p300.move_to(bypass) 
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

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
            if TIPMIX == 'YES':
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
        if TIPMIX == 'NO':
            protocol.pause('Shake 1 min')

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
            p300_dispose(200)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #1')
        ETOHMaxVol = 150
        ETOHCount = 0
        for loop, X in enumerate(column_1_list):
            p300_pick_up_tip()
            if ETOHCount <= 5:
                p300.aspirate(ETOHMaxVol, EtOH_1.bottom())
            else:
                p300.aspirate(ETOHMaxVol, EtOH_2.bottom())
            ETOHCount += 1
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
            p300_dispose(200)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        protocol.comment('--> ETOH Wash #2')
        ETOHMaxVol = 150
        ETOHCount = 0
        for loop, X in enumerate(column_1_list):
            p300_pick_up_tip()
            if ETOHCount <= 5:
                p300.aspirate(ETOHMaxVol, EtOH_3.bottom())
            else:
                p300.aspirate(ETOHMaxVol, EtOH_4.bottom())
            ETOHCount += 1
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
            p300_dispose(200)
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
            if TIPMIX == 'YES':
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
        if TIPMIX == 'NO':
            protocol.pause('Shake 1 min')

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
            p300_dispose(200)
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
            p300_dispose(200)
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
            p300.dispense(TransferSup+5, sample_plate_final[column_2_list[loop]].bottom())
            p300.move_to(bypass)
            p300.drop_tip() if DRYRUN == 'NO' else p300.return_tip()

        if DRYRUN == 'NO':
            protocol.comment('MAGNET DISENGAGE')
            mag_block.disengage()
