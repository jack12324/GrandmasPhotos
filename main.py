import PySimpleGUI as sg
import os
from PIL import Image, ImageTk
import io

import ImageStateLoader
from ImageState import ImageState

START_FOLDER = "C:/Users/Jacks/Programming/GrandmasPhotos/Photos/Tif/Denny"

file_states = ImageStateLoader.load_image_states()

# Get the folder containing the images from the user
if START_FOLDER == "":
    folder = sg.popup_get_folder('Start Folder', default_path='')
else:
    folder = START_FOLDER

print(folder)

if not folder:
    sg.popup_cancel('Cancelling')
    raise SystemExit()


# returns array of path to all tif files in a given directory
# also searches subdirectories
def get_all_tif_files(start_path):
    tif_files = []
    lfiles = os.listdir(start_path)
    for file in lfiles:
        file_path = os.path.join(start_path, file)
        if os.path.isfile(file_path):
            if file.endswith(".tif"):
                tif_files.append(file_path)
        else:
            tif_files.extend(get_all_tif_files(file_path))
    return tif_files


all_tifs = get_all_tif_files(folder)

uninitialized = []
convert_queue = []
upload_queue = []
unrotated = []


def sort_tifs():
    for tif in all_tifs:
        if tif in file_states:
            if file_states[tif].rotated:
                if file_states[tif].converted:
                    if file_states[tif].uploaded:
                        continue
                    else:
                        upload_queue.append(tif)
                else:
                    convert_queue.append(tif)
            else:
                unrotated.append(tif)
        else:
            file_states[tif] = ImageState()
            unrotated.append(tif)


sort_tifs()

num_files = len(unrotated)  # number of iamges found
if num_files == 0:
    sg.popup('No files in folder')
    raise SystemExit()


# ------------------------------------------------------------------------------
# use PIL to read data of one image
# ------------------------------------------------------------------------------


def get_img_data(file_path, rotate=0, maxsize=(800, 800), first=False):
    """Generate image data using PIL
    """
    img = Image.open(file_path)
    img.thumbnail(maxsize)
    if rotate != 0:
        if rotate == 90:
            img = img.transpose(Image.ROTATE_90)
        elif rotate == 180:
            img = img.transpose(Image.ROTATE_180)
        else:
            img = img.transpose(Image.ROTATE_270)

    if first:  # tkinter is inactive the first time
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()
    return ImageTk.PhotoImage(img)


# ------------------------------------------------------------------------------


# make these 2 elements outside the layout as we want to "update" them later
# initialize to the first file in the list
filename = unrotated[0]  # name of first file in list
image_elem = sg.Image(data=get_img_data(filename, first=True))
filename_display_elem = sg.Text(filename, auto_size_text=True)
file_num_display_elem = sg.Text('File 1 of {}'.format(num_files), size=(15, 1))

# define layout, show and read the form
col = [[filename_display_elem],
       [image_elem]]

col_files = [[sg.Listbox(values=unrotated, change_submits=True, size=(60, 30), key='listbox')],
             [sg.Button('Save and Next', size=(8, 2)), sg.Button('Prev', size=(8, 2)), file_num_display_elem],
             [sg.Button('Rotate Left', size=(8, 4)), sg.Button('Rotate Right', size=(8, 4))],
             [sg.Button('Show Metadata'), sg.Button('Clear Metadata')]]

layout = [[sg.Column(col_files, vertical_alignment="top"),
           sg.Column(col, element_justification="left", vertical_alignment="top")]]

window = sg.Window('Image Browser', layout, return_keyboard_events=True,
                   location=(0, 0), use_default_focus=False, resizable=True)

# loop reading the user input and displaying image, filename
i = 0
rotate_value = 0


def rotate_image(file_path, rotate):
    img = Image.open(file_path)
    if rotate == 90:
        img = img.transpose(Image.ROTATE_90)
    elif rotate == 180:
        img = img.transpose(Image.ROTATE_180)
    else:
        img = img.transpose(Image.ROTATE_270)

    img.save(file_path)
    file_states[file_path].rotated = True


while True:
    # read the form
    event, values = window.read()
    print(event, values)
    # perform button and keyboard operations
    if event == sg.WIN_CLOSED:
        ImageStateLoader.save_image_states(file_states)
        break
    elif event in 'Save and Next':
        if rotate_value % 360 != 0:
            rotate_image(filename, rotate_value % 360)
        rotate_value = 0
        i += 1
        if i >= num_files:
            i -= num_files
        filename = unrotated[i]
    elif event in 'Prev':
        rotate_value = 0
        i -= 1
        if i < 0:
            i = num_files + i
        filename = unrotated[i]
    elif event == 'listbox':  # something from the listbox
        rotate_value = 0
        f = values["listbox"][0]  # selected filename
        filename = f  # read this file
        i = unrotated.index(f)  # update running index
    elif event == 'Rotate Right':
        rotate_value -= 90
    elif event == 'Rotate Left':
        rotate_value += 90
    elif event == 'Show Metadata':
        print(file_states[filename])
    elif event == 'Clear Metadata':
        pass
    else:
        filename = unrotated[i]

    # update window with new image
    image_elem.update(data=get_img_data(filename, rotate=(rotate_value % 360), first=True))
    # update window with filename
    filename_display_elem.update(filename)
    # update page display
    file_num_display_elem.update('File {} of {}'.format(i + 1, num_files))

window.close()
