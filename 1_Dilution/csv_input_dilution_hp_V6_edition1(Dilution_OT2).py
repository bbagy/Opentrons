import os
import csv
import json
from tkinter import filedialog
from tkinter import Tk, StringVar, Entry, Button, Toplevel, Label


# Setup the window
root = Tk()
root.title("Dilution With Heekuk!!")
root.geometry("750x100")

# Label, Button, and Text Entry for source file
source_file_label = Label(root, text="Select input CSV file:")
source_file_label.grid(row=0, column=0)
source_file_path = StringVar()
source_file_entry = Entry(root, textvariable=source_file_path, width=50)
source_file_entry.grid(row=0, column=1)

# Label, Button, and Text Entry for destination file
dest_file_label = Label(root, text="Select output Python file:")
dest_file_label.grid(row=1, column=0)
dest_file_path = StringVar()
dest_file_entry = Entry(root, textvariable=dest_file_path, width=50)
dest_file_entry.grid(row=1, column=1)

def browse_file():
    filename = filedialog.askopenfilename()
    source_file_path.set(filename)
    # Set the default output file name and location based on the input CSV file
    dest_file_path.set(os.path.splitext(filename)[0] + '_ot2_protocol.py')

def browse_dest_file():
    filename = filedialog.asksaveasfilename(defaultextension=".py")
    dest_file_path.set(filename)

source_browse_button = Button(root, text="Select", command=browse_file)
source_browse_button.grid(row=0, column=2)

dest_file_browse_button = Button(root, text="Select", command=browse_dest_file)
dest_file_browse_button.grid(row=1, column=2)



# Define the protocol template
template = """
def get_values(*names):
    import json
    _all_values = json.loads('{"p300_mount":"right"}')
    return [_all_values[n] for n in names]


# metadata
metadata = {
    'protocolName': '(Delete this protocol after use) Water Transfer with CSV File',
    'author': 'Heekuk Park <hp2523@cumc.columbia.edu>',
    'source': 'Custom Protocol',
    'apiLevel': '2.7'
}

def run(protocol):

    p300_mount = 'right'  # change to 'left' if you are using left

    # load Labware
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', '6')

    reservoir = protocol.load_labware('opentrons_10_tuberack_nest_4x50ml_6x15ml_conical', '5')
    plate = protocol.load_labware('{{plate}}', '2')

    # load instrument
    p300 = protocol.load_instrument('p300_single_gen2', p300_mount, tip_racks=[tiprack_300])

    # csv data --> nested list
    transfer = {{csv_data}}
    total_volume = 0
    for line in transfer:
        sample, dna_vol, water_vol, well = line
        total_volume += water_vol


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
"""
# Define function to compile
def compile():
    # Check if the input CSV and output Python file paths are specified
    if not source_file_path.get() or not dest_file_path.get():
        error_window = Toplevel(root)
        error_window.title("Error")
        error_label = Label(error_window, text="Please specify both the input CSV file and the output Python file.")
        error_label.pack()
        ok_button = Button(error_window, text="OK", command=error_window.destroy)
        ok_button.pack()
        return  # Return early without doing anything else

    source_file = source_file_path.get()
    dest_file = dest_file_path.get()

    total_volume = 0
    max_volume = 0

    csv_data = []

    with open(source_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # skip the headers

        for row in reader:
            sample, dna_vol, water_vol, well = row
            water_vol = float(water_vol)
            csv_data.append([sample, float(dna_vol), water_vol, well])

            total_volume += water_vol
            max_volume = max(max_volume, water_vol)

    # Convert volumes to ml and round to 2 decimal places
    total_volume = round(total_volume / 1000, 2)  # Assuming your volumes are in µL
    max_volume = round(max_volume / 1000, 2)  # Assuming your volumes are in µL

    # Plate recommendation logic
    if max_volume <= 0.2:
        plate = 'biorad_96_wellplate_200ul_pcr'
    else:
        plate = 'nest_96_wellplate_2ml_deep'

    # Open destination file and write
    with open(dest_file, 'w') as file:
        file.write(template.replace('{{plate}}', plate).replace('{{csv_data}}', json.dumps(csv_data)))

    # Open a new window with suggestions and information
    info_window = Toplevel(root)
    info_window.title("Heekuk’s Suggestion")
    info_label = Label(info_window, text=f"Max Volume: {max_volume}ml\nTotal Volume: {total_volume}ml\nRecommended Plate: {plate}")
    info_label.pack()
    ok_button = Button(info_window, text="OK", command=info_window.destroy)
    ok_button.pack()
    
# Function to reset
def reset():
    source_file_path.set('')
    dest_file_path.set('')

# Function to quit
def quit():
    root.destroy()


# Compile button
compile_button = Button(root, text="Compile", command=compile)
compile_button.grid(row=2, column=1)

# Reset button
reset_button = Button(root, text="Reset", command=reset)
reset_button.grid(row=2, column=0)

# Quit button
quit_button = Button(root, text="Quit", command=quit)
quit_button.grid(row=2, column=2)

# Run the tkinter mainloop
root.mainloop()
