
def get_values(*names):
    import json
    _all_values = json.loads('{"p300_mount":"right"}')
    return [_all_values[n] for n in names]


# metadata
metadata = {
    'protocolName': 'Water Transfer with CSV File',
    'author': 'Heekuk Park <hp2523@cumc.columbia.edu>',
    'source': 'Custom Protocol',
    'apiLevel': '2.7'
}

def run(protocol):

    p300_mount = 'right'  # change to 'left' if you are using left

    # load Labware
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', '6')

    reservoir = protocol.load_labware('opentrons_10_tuberack_nest_4x50ml_6x15ml_conical', '5')
    plate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', '2')

    # load instrument
    p300 = protocol.load_instrument('p300_single_gen2', p300_mount, tip_racks=[tiprack_300])

    # csv data --> nested list
    transfer = [["A1", 1.0, 29.0, "A1", 30.0], ["B1", 2.0, 28.0, "B1", 30.0], ["C1", 3.0, 27.0, "C1", 30.0], ["D1", 4.0, 26.0, "D1", 30.0], ["E1", 5.0, 25.0, "E1", 30.0], ["F1", 6.0, 24.0, "F1", 30.0], ["G1", 7.0, 23.0, "G1", 30.0], ["H1", 8.0, 22.0, "H1", 30.0], ["A2", 9.0, 21.0, "A2", 30.0], ["B2", 10.0, 20.0, "B2", 30.0], ["C2", 11.0, 19.0, "C2", 30.0], ["D2", 12.0, 18.0, "D2", 30.0], ["E2", 13.0, 17.0, "E2", 30.0], ["F2", 14.0, 16.0, "F2", 30.0], ["G2", 15.0, 15.0, "G2", 30.0], ["H2", 16.0, 14.0, "H2", 30.0], ["A3", 17.0, 13.0, "A3", 30.0], ["B3", 18.0, 12.0, "B3", 30.0], ["C3", 19.0, 11.0, "C3", 30.0], ["D3", 20.0, 10.0, "D3", 30.0], ["E3", 21.0, 9.0, "E3", 30.0], ["F3", 22.0, 8.0, "F3", 30.0], ["G3", 23.0, 7.0, "G3", 30.0], ["H3", 24.0, 6.0, "H3", 30.0], ["A4", 25.0, 5.0, "A4", 30.0], ["B4", 26.0, 4.0, "B4", 30.0], ["C4", 27.0, 3.0, "C4", 30.0], ["D4", 28.0, 2.0, "D4", 30.0], ["E4", 29.0, 1.0, "E4", 30.0], ["F4", 30.0, 0.0, "F4", 30.0], ["G4", 1.0, 29.0, "G4", 30.0], ["H4", 2.0, 28.0, "H4", 30.0], ["A5", 3.0, 27.0, "A5", 30.0], ["B5", 4.0, 26.0, "B5", 30.0], ["C5", 5.0, 25.0, "C5", 30.0], ["D5", 6.0, 24.0, "D5", 30.0], ["E5", 7.0, 23.0, "E5", 30.0], ["F5", 8.0, 22.0, "F5", 30.0], ["G5", 9.0, 21.0, "G5", 30.0], ["H5", 10.0, 20.0, "H5", 30.0], ["A6", 11.0, 19.0, "A6", 30.0], ["B6", 12.0, 18.0, "B6", 30.0], ["C6", 13.0, 17.0, "C6", 30.0], ["D6", 14.0, 16.0, "D6", 30.0], ["E6", 15.0, 15.0, "E6", 30.0], ["F6", 16.0, 14.0, "F6", 30.0], ["G6", 17.0, 13.0, "G6", 30.0], ["H6", 18.0, 12.0, "H6", 30.0], ["A7", 19.0, 11.0, "A7", 30.0], ["B7", 20.0, 10.0, "B7", 30.0], ["C7", 21.0, 9.0, "C7", 30.0], ["D7", 22.0, 8.0, "D7", 30.0], ["E7", 23.0, 7.0, "E7", 30.0], ["F7", 24.0, 6.0, "F7", 30.0], ["G7", 25.0, 5.0, "G7", 30.0], ["H7", 26.0, 4.0, "H7", 30.0], ["A8", 27.0, 3.0, "A8", 30.0], ["B8", 28.0, 2.0, "B8", 30.0], ["C8", 29.0, 1.0, "C8", 30.0], ["D8", 30.0, 0.0, "D8", 30.0], ["E8", 1.0, 29.0, "E8", 30.0], ["F8", 2.0, 28.0, "F8", 30.0], ["G8", 3.0, 27.0, "G8", 30.0], ["H8", 4.0, 26.0, "H8", 30.0], ["A9", 5.0, 25.0, "A9", 30.0], ["B9", 6.0, 24.0, "B9", 30.0], ["C9", 7.0, 23.0, "C9", 30.0], ["D9", 8.0, 22.0, "D9", 30.0], ["E9", 9.0, 21.0, "E9", 30.0], ["F9", 10.0, 20.0, "F9", 30.0], ["G9", 11.0, 19.0, "G9", 30.0], ["H9", 12.0, 18.0, "H9", 30.0], ["A10", 13.0, 17.0, "A10", 30.0], ["B10", 14.0, 16.0, "B10", 30.0], ["C10", 15.0, 15.0, "C10", 30.0], ["D10", 16.0, 14.0, "D10", 30.0], ["E10", 17.0, 13.0, "E10", 30.0], ["F10", 18.0, 12.0, "F10", 30.0], ["G10", 19.0, 11.0, "G10", 30.0], ["H10", 20.0, 10.0, "H10", 30.0], ["A11", 21.0, 9.0, "A11", 30.0], ["B11", 22.0, 8.0, "B11", 30.0], ["C11", 23.0, 7.0, "C11", 30.0], ["D11", 24.0, 6.0, "D11", 30.0], ["E11", 25.0, 5.0, "E11", 30.0], ["F11", 26.0, 4.0, "F11", 30.0], ["G11", 27.0, 3.0, "G11", 30.0], ["H11", 28.0, 2.0, "H11", 30.0], ["A12", 29.0, 1.0, "A12", 30.0], ["B12", 30.0, 0.0, "B12", 30.0], ["C12", 1.0, 29.0, "C12", 30.0], ["D12", 2.0, 28.0, "D12", 30.0], ["E12", 3.0, 27.0, "E12", 30.0], ["F12", 4.0, 26.0, "F12", 30.0], ["G12", 5.0, 25.0, "G12", 30.0], ["H12", 6.0, 24.0, "H12", 30.0]]

    for line in transfer:
        sample, dna_vol, water_vol, well, total_volume_row = line

    # Total volume of water and initial tip height
    total_volume = 0
    tip_height = total_volume / 200  # Calculate initial tip height based on total volume (assumption: reservoir diameter is 38mm)

    for line in transfer:
        if not p300.has_tip:
            p300.pick_up_tip()
        vol_water = float(line[2]) # add column 2 of volume
        well = line[3]
        
        p300.flow_rate.blow_out = 150
        
        # Calculate z based on the remaining volume
        z = max(5, total_volume / 50 * 45 - 7.2)  # Assuming the height of the reservoir is 45mm and we should stay 7.2mm from the top

        if vol_water > p300.max_volume:
            # If the volume exceeds the pipette's maximum volume, transfer in multiple steps
            num_transfers = int(vol_water / p300.max_volume)
            remainder = vol_water % p300.max_volume
            
            for _ in range(num_transfers):
                p300.transfer(p300.max_volume, reservoir['B4'].bottom(z=z),
                              plate.wells_by_name()[well].bottom(z=5), new_tip='never')
            
            if remainder > 0:
                p300.transfer(remainder, reservoir['B4'].bottom(z=z),
                              plate.wells_by_name()[well].bottom(z=5), new_tip='never')
        else:
            p300.transfer(vol_water, reservoir['B4'].bottom(z=z),
                          plate.wells_by_name()[well].bottom(z=5), new_tip='never')
                        
        # Update the remaining volume and tip height for the next loop iteration
        p300.blow_out(plate.wells_by_name()[well].bottom(z=5))
        total_volume -= vol_water
        tip_height = total_volume / 200  # Update tip height based on remaining volume

    if p300.has_tip:
        p300.drop_tip()
