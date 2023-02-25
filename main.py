import time

import PySimpleGUI as sg
import os
from PIL import Image, ImageTk
import io

import ImageStateLoader
from ImageState import ImageState

START_FOLDER = "E:\Files\Python Scripts\GrandmasPhotos\Photos\Denny"


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

previous_queue = []
convert_queue = []
upload_queue = []
unrotated = []


def convert_image(image_path):
    # importing the image
    filename = image_path.replace("Tif", "Jpg")
    filename = filename.replace("tif", "jpg")
    if not os.path.isdir(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    if not os.path.isfile(filename):
        im = Image.open(image_path)
        # converting to jpg
        rgb_im = im.convert("RGB")
        # exporting the image
        rgb_im.save(filename, quality=95)

def convert_all_rotated():
    print(convert_queue)
    while len(convert_queue) > 0:
        image = convert_queue.pop()
        convert_image(image)
        file_states[image].converted = True
        if image not in upload_queue:
            upload_queue.append(image)
    ImageStateLoader.save_image_states(file_states)



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

if (len(unrotated) + len(convert_queue) + len(upload_queue))== 0:
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
if len(unrotated) == 0:
    filename = "default_image.jpg"
else:
    filename = unrotated[0]  # name of first file in list
image_elem = sg.Image(data=get_img_data(filename, first=True))
filename_display_elem = sg.Text(filename, auto_size_text=True)
if len(unrotated) == 0:
    num_to_rotate_display = sg.Text('No Unrotated Files', size=(15, 1))
else:
    num_to_rotate_display = sg.Text('Unrotated File 1 of {}'.format(len(unrotated)), size=(15, 1))

num_to_convert_display = sg.Text('Images to Convert: {}'.format(len(convert_queue)), size=(15, 1))
num_to_upload_display = sg.Text('Images to Upload: {}'.format(len(upload_queue)), size=(15, 1))

# define layout, show and read the form
col = [[filename_display_elem],
       [image_elem]]

col_files = [[num_to_rotate_display],
             [num_to_convert_display],
             [num_to_upload_display],
             [sg.Button('Rotate Left', size=(8, 4)), sg.Button('Rotate Right', size=(8, 4))],
             [sg.Button('Prev', size=(8, 2)), sg.Button('Confirm Rotation', size=(8, 2))],
             [sg.Button('Show File State'), sg.Button('Convert Rotated to Jpg')]]

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


while True:
    # read the form
    event, values = window.read()
    print(event, values)
    # perform button and keyboard operations
    if event == sg.WIN_CLOSED:
        ImageStateLoader.save_image_states(file_states)
        break
    elif event == 'Confirm Rotation':
        if len(unrotated) == 0:
            continue
        if rotate_value % 360 != 0:
            rotate_image(filename, rotate_value % 360)
        file_states[filename].rotated = True
        file_states[filename].converted = False
        file_states[filename].uploaded = False
        if filename not in convert_queue:
            convert_queue.append(filename)
        if filename in upload_queue:
            upload_queue.remove(filename)
        previous_queue.append(filename)
        unrotated.remove(filename)
        rotate_value = 0
        if len(unrotated) == 0:
            filename = "default_image.jpg"
        else:
            filename = unrotated[0]
    elif event == 'Prev':
        if len(previous_queue) == 0:
            continue
        rotate_value = 0
        unrotated.insert(0, previous_queue.pop())
        filename = unrotated[0]
        file_states[filename].rotated = False
        file_states[filename].converted = False
        file_states[filename].uploaded = False
        if filename in convert_queue:
            convert_queue.remove(filename)
        if filename in upload_queue:
            upload_queue.remove(filename)
    elif event == 'Rotate Right':
        if len(unrotated) == 0:
            continue
        rotate_value -= 90
    elif event == 'Rotate Left':
        if len(unrotated) == 0:
            continue
        rotate_value += 90
    elif event == 'Show File State':
        if len(unrotated) == 0:
            continue
        print(file_states[filename])
    elif event == "Convert Rotated to Jpg":
        window.start_thread(lambda: convert_all_rotated(), ('-THREAD', '-THREAD ENDED-'))
    else:
        if len(unrotated) == 0:
            filename = "default_image.jpg"
        else:
            filename = unrotated[0]

    # update window with new image
    image_elem.update(data=get_img_data(filename, rotate=(rotate_value % 360), first=True))
    # update window with filename
    filename_display_elem.update(filename)
    # update page display
    if len(unrotated) == 0:
        num_to_rotate_display.update('No Unrotated Files')
    else:
        num_to_rotate_display.update('File {} of {}'.format(i + 1, len(unrotated)))

    num_to_convert_display.update('Images to Convert: {}'.format(len(convert_queue)))
    num_to_upload_display.update('Images to Upload: {}'.format(len(upload_queue)))

window.close()
