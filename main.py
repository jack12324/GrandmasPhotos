import json
import PySimpleGUI as sg
import os

import pyexif as pyexif
from PIL import Image, ImageTk
import io
from State import State

# Get the folder containing the images from the user
folder = sg.popup_get_folder('Start Folder', default_path='')
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


fnames = get_all_tif_files(folder)

num_files = len(fnames)  # number of iamges found
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
filename = fnames[0]  # name of first file in list
image_elem = sg.Image(data=get_img_data(filename, first=True))
filename_display_elem = sg.Text(filename, auto_size_text=True)
file_num_display_elem = sg.Text('File 1 of {}'.format(num_files), size=(15, 1))

# define layout, show and read the form
col = [[filename_display_elem],
       [image_elem]]

col_files = [[sg.Listbox(values=fnames, change_submits=True, size=(60, 30), key='listbox')],
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
    exif = pyexif.ExifEditor(file_path)
    tag = exif.getTag("UserComment")

    if tag is None:
        init_metadata(exif)

    try:
        status = json.loads(exif.getTag("UserComment"))
    except TypeError:
        init_metadata(exif)
        status = json.loads(exif.getTag("UserComment"))

    img = Image.open(file_path)
    if rotate == 90:
        img = img.transpose(Image.ROTATE_90)
    elif rotate == 180:
        img = img.transpose(Image.ROTATE_180)
    else:
        img = img.transpose(Image.ROTATE_270)

    img.save(file_path)

    status[State.ROTATED.value] = True
    # Assume that if we are rotating the image that it needs to be re converted and uploaded
    status[State.CONVERTED.value] = False
    exif.setTag("UserComment", json.dumps(status))


def show_metadata(path):
    exif = pyexif.ExifEditor(path)
    tag = exif.getTag("UserComment")
    if tag is None:
        init_metadata(exif)
    tag = exif.getTag("UserComment")
    print(tag)


def init_metadata(exif):
    status = {State.ROTATED.value: False, State.CONVERTED.value: False}
    exif.setTag("UserComment", json.dumps(status))


while True:
    # read the form
    event, values = window.read()
    print(event, values)
    # perform button and keyboard operations
    if event == sg.WIN_CLOSED:
        break
    elif event in 'Save and Next':
        if rotate_value % 360 != 0:
            rotate_image(filename, rotate_value % 360)
        rotate_value = 0
        i += 1
        if i >= num_files:
            i -= num_files
        filename = fnames[i]
    elif event in 'Prev':
        rotate_value = 0
        i -= 1
        if i < 0:
            i = num_files + i
        filename = fnames[i]
    elif event == 'listbox':  # something from the listbox
        rotate_value = 0
        f = values["listbox"][0]  # selected filename
        filename = f  # read this file
        i = fnames.index(f)  # update running index
    elif event == 'Rotate Right':
        rotate_value -= 90
    elif event == 'Rotate Left':
        rotate_value += 90
    elif event == 'Show Metadata':
        show_metadata(filename)
    elif event == 'Clear Metadata':
        metadata = pyexif.ExifEditor(filename)
        init_metadata(metadata)
    else:
        filename = fnames[i]

    # update window with new image
    image_elem.update(data=get_img_data(filename, rotate=(rotate_value % 360), first=True))
    # update window with filename
    filename_display_elem.update(filename)
    # update page display
    file_num_display_elem.update('File {} of {}'.format(i + 1, num_files))

window.close()
