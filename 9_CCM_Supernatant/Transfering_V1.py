from tkinter import Tk, StringVar, Entry, Button, Toplevel, Label, filedialog
import os
import json
from tkinter import filedialog


# Setup the window
root = Tk()
root.title("Transferring with Heekuk Using DWP")
root.geometry("800x200")

# Label, and Text Entry for aspiration height
asp_height_label = Label(root, text="Enter aspiration height:")
asp_height_label.grid(row=0, column=0)
asp_height = StringVar()
asp_height_entry = Entry(root, textvariable=asp_height)
asp_height_entry.grid(row=0, column=1)

# Label, and Text Entry for transfer volume
transfer_vol_label = Label(root, text="Enter transfer volume:")
transfer_vol_label.grid(row=1, column=0)
transfer_vol = StringVar()
transfer_vol_entry = Entry(root, textvariable=transfer_vol)
transfer_vol_entry.grid(row=1, column=1)

# Label, Button, and Text Entry for destination file
dest_file_label = Label(root, text="Select output Python file:")
dest_file_label.grid(row=2, column=0)
dest_file_path = StringVar()
dest_file_entry = Entry(root, textvariable=dest_file_path, width=50)
dest_file_entry.grid(row=2, column=1)

def browse_dest_file():
    filename = filedialog.asksaveasfilename(defaultextension=".py")
    dest_file_path.set(filename)

dest_file_browse_button = Button(root, text="Select", command=browse_dest_file)
dest_file_browse_button.grid(row=2, column=2)

template = '''
def get_values(*names):
    import json
    _all_values = json.loads("""{"asp_height":variablefrom GUI,"transfer_vol":variablefrom GUI,asp_speed":100,"disp_speed":100,"disp_height":10, "max_vol":300}""")
    return [_all_values[n] for n in names]

metadata = {
    'protocolName': 'variablefrom GUI',
    'author': 'Heekuk Park <sakib.hossain@opentrons.com>',
    'source': 'Custom Protocol in Uhlemann Lab',
    'apiLevel': '2.8'
}

def run(protocol):
    [asp_speed, disp_speed, asp_height, disp_height, transfer_vol, max_vol] = get_values('asp_speed', 'disp_speed', 'asp_height', 'disp_height', 'transfer_vol', 'max_vol')

    # load Labware
    plate1 = protocol.load_labware('waters_96_wellplate_2ml', 5, 'Plate 1')
    plate2 = protocol.load_labware('waters_96_wellplate_2ml', 8, 'Plate 2')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 2)

    # load instrument
    m300 = protocol.load_instrument('p300_multi_gen2', 'right', tip_racks=[tiprack])

    # Get sample columns
    plate1_wells = plate1.rows()[0]
    plate2_wells = plate2.rows()[0]

    # Flow Rates
    m300.flow_rate.aspirate = asp_speed
    m300.flow_rate.dispense = disp_speed

    # Transfer transfer_vol uL to Plate 2
    for p1_well, p2_well in zip(plate1_wells, plate2_wells):
        m300.pick_up_tip()

        remaining_vol = transfer_vol
        while remaining_vol > 0:
            vol_to_transfer = min(remaining_vol, max_vol)
            m300.aspirate(vol_to_transfer, p1_well.bottom(z=asp_height), air_gap=30)
            m300.dispense(vol_to_transfer, p2_well.bottom(z=disp_height))
            m300.blow_out(p2_well)  # Blow out to ensure complete dispensing
            remaining_vol -= vol_to_transfer

        m300.drop_tip()
'''

# Define function to compile
def compile():
    # Check if the transfer volume and aspiration height are specified
    if not asp_height.get() or not transfer_vol.get() or not dest_file_path.get():
        error_window = Toplevel(root)
        error_window.title("Error")
        error_label = Label(error_window, text="Please specify the aspiration height, transfer volume, and the output Python file.")
        error_label.pack()
        ok_button = Button(error_window, text="OK", command=error_window.destroy)
        ok_button.pack()
        return  # Return early without doing anything else

    dest_file = dest_file_path.get()

    # Convert the aspiration height and transfer volume to floats
    asp_height_float = float(asp_height.get())
    transfer_vol_float = float(transfer_vol.get())

    # Open destination file and write
    with open(dest_file, 'w') as file:
        file.write(template.replace('"asp_height":10', '"asp_height":' + str(asp_height_float)).replace('"transfer_vol":300', '"transfer_vol":' + str(transfer_vol_float)))

def browse_file():
    filename = filedialog.asksaveasfilename(defaultextension=".py")
    dest_file_path.set(filename)

browse_button = Button(root, text="Browse", command=browse_file)
browse_button.grid(row=2, column=2)



# Function to reset
def reset():
    asp_height.set('')
    transfer_vol.set('')
    dest_file_path.set('')

# Function to quit
def quit():
    root.destroy()

pipette_info = Label(root, text="This script is designed for a p300_multi_gen2 pipette attached to the right mount.")
pipette_info.grid(row=4, column=0, columnspan=3)


# Compile button
compile_button = Button(root, text="Compile", command=compile)
compile_button.grid(row=3, column=1)

# Reset button
reset_button = Button(root, text="Reset", command=reset)
reset_button.grid(row=3, column=0)

# Quit button
quit_button = Button(root, text="Quit", command=quit)
quit_button.grid(row=3, column=2)

# Run the tkinter mainloop
root.mainloop()



It seems fine to me but the compile button is overlap "Enter protocol name".
