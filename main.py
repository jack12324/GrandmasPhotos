import os.path

import PySimpleGUI as sg
from PIL import Image, ImageTk
import io
import cv2


from PySimpleGUI import Window

from GoogleDriveHandler import GoogleDriveHandler
from ImageStateHandler import ImageStateHandler

START_FOLDER = ''#"D:\\Files\\Python Scripts\\GrandmasPhotos\\Photos\\Denny"


def main():
    # Get the folder containing the images from the user
    if START_FOLDER == "":
        folder = sg.popup_get_folder('Start Folder', default_path='')
    else:
        folder = START_FOLDER

    print(folder)

    # Exit program if folder doesn't exist
    if not folder:
        sg.popup_cancel('Cancelling')
        raise SystemExit()

    upload_handler = GoogleDriveHandler()
    image_handler = ImageStateHandler(folder, upload_handler)



    # If there is nothing for the program to do, exit
    if (
            image_handler.get_num_to_rotate() +
            image_handler.get_num_to_convert() +
            image_handler.get_num_to_upload()) == 0:
        sg.popup('No files in folder')
        raise SystemExit()
    # ------------------------------------------------------------------------------

    filename = image_handler.get_display_image()

    # make these 2 elements outside the layout as we want to "update" them later
    # initialize to the first file in the list
    image_elem = sg.Image(data=get_img_data(filename, first=True))
    filename_display_elem = sg.Text(filename, auto_size_text=True)

    num_to_rotate_display = sg.Text('Images to Rotate {}'.format(image_handler.get_num_to_rotate()), size=(19, 1))
    num_to_convert_display = sg.Text('Images to Convert: {}'.format(image_handler.get_num_to_convert()), size=(19, 1))
    num_to_upload_display = sg.Text('Images to Upload: {}'.format(image_handler.get_num_to_upload()), size=(19, 1))

    # define layout, show and read the form
    col = [[filename_display_elem],
           [image_elem]]

    col_files = [[num_to_rotate_display],
                 [num_to_convert_display],
                 [num_to_upload_display],
                 [sg.Button('Rotate Left', size=(8, 4)), sg.Button('Rotate Right', size=(8, 4))],
                 [sg.Button('Prev', size=(8, 2)), sg.Button('Confirm Rotation', size=(8, 2))],
                 [sg.Button('Show File State'), sg.Button('Convert Rotated to Jpg'), sg.Button('Upload Converted')]]

    layout = [[sg.Column(col_files, vertical_alignment="top"),
               sg.Column(col, element_justification="left", vertical_alignment="top")]]

    window = sg.Window('Image Browser', layout, return_keyboard_events=True,
                       location=(0, 0), use_default_focus=False, resizable=True)

    # initialize buttons as enabled or disabled. Set initial button rotation to 0
    window.finalize()
    set_display_dependent_button_enables(window, image_handler.get_num_to_rotate() != 0)
    set_convert_dependent_button_enables(window, image_handler.get_num_to_convert() != 0)
    set_previous_dependent_button_enables(window, image_handler.get_num_rotated() != 0)
    set_upload_dependent_button_enables(window, image_handler.get_num_to_upload() != 0)
    rotate_value = 0

    while True:
        # read the form
        event, values = window.read()
        print(event, values)
        # If the program exists we want to save our current image states
        if event == sg.WIN_CLOSED:
            image_handler.save_image_states()
            break
        # If we confirm rotation, we rotate the image if needed, then tell the image handler the image has been
        # rotated. Finally, we update what image to display, and update whether any buttons should be disabled
        elif event == 'Confirm Rotation':
            if rotate_value % 360 != 0:
                rotate_image(filename, rotate_value % 360, image_handler, window)
            image_handler.image_rotated(filename)
            rotate_value = 0
            filename = image_handler.get_display_image()
            set_display_dependent_button_enables(window, image_handler.get_num_to_rotate() != 0)
            set_previous_dependent_button_enables(window, image_handler.get_num_rotated() != 0)
            set_convert_dependent_button_enables(window, image_handler.get_num_to_convert() != 0)
        elif event == 'Prev':
            image_handler.reset_previous()
            filename = image_handler.get_display_image()
            set_display_dependent_button_enables(window, image_handler.get_num_to_rotate() != 0)
            set_previous_dependent_button_enables(window, image_handler.get_num_rotated() != 0)
            set_convert_dependent_button_enables(window, image_handler.get_num_to_convert() != 0)
            set_upload_dependent_button_enables(window, image_handler.get_num_to_upload() != 0)
            rotate_value = 0
        elif event == 'Rotate Right':
            rotate_value -= 90
        elif event == 'Rotate Left':
            rotate_value += 90
        elif event == 'Show File State':
            print(image_handler.get_file_state(filename))
        elif event == 'Upload Converted':
            image_handler.upload_all_converted()
            set_upload_dependent_button_enables(window, image_handler.get_num_to_upload() != 0)
        elif event == "Convert Rotated to Jpg":
            set_convert_dependent_button_enables(window, False)
            window.start_thread(lambda: image_handler.convert_all_rotated(), ('-THREAD-', '-THREAD ENDED-'))
        elif event[0] == '-THREAD-':
            if event[1] == '-THREAD ENDED-':
                set_convert_dependent_button_enables(window, image_handler.get_num_to_convert() != 0)
                set_upload_dependent_button_enables(window, image_handler.get_num_to_upload() != 0)
        else:
            filename = image_handler.get_display_image()

        # update window with new image
        image_elem.update(data=get_img_data(filename, rotate=(rotate_value % 360), first=True))
        # update window with filename
        filename_display_elem.update(filename)
        # update page display

        num_to_rotate_display.update('Images to Rotate: {}'.format(image_handler.get_num_to_rotate()))
        num_to_convert_display.update('Images to Convert: {}'.format(image_handler.get_num_to_convert()))
        num_to_upload_display.update('Images to Upload: {}'.format(image_handler.get_num_to_upload()))

    window.close()


def set_display_dependent_button_enables(window: Window, enabled: bool) -> None:
    window['Rotate Right'].update(disabled=(not enabled))
    window['Rotate Left'].update(disabled=(not enabled))
    window['Show File State'].update(disabled=(not enabled))
    window['Confirm Rotation'].update(disabled=(not enabled))


def set_convert_dependent_button_enables(window: Window, enabled: bool) -> None:
    window['Convert Rotated to Jpg'].update(disabled=(not enabled))


def set_previous_dependent_button_enables(window: Window, enabled: bool) -> None:
    window['Prev'].update(disabled=(not enabled))


def set_upload_dependent_button_enables(window: Window, enabled: bool) -> None:
    window['Upload Converted'].update(disabled=(not enabled))


def rotate_image(file_path: str, rotate: int, image_handler: ImageStateHandler, window) -> None:

    original_size = os.path.getsize(file_path)
    src = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

    if rotate == 90:
        img = cv2.rotate(src, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rotate == 180:
        img = cv2.rotate(src, cv2.ROTATE_180)
    else:
        img = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)

    cv2.imwrite(file_path, img, params=(cv2.IMWRITE_TIFF_COMPRESSION, 1))
    after_size = os.path.getsize(file_path)
    size_diff_kb = (after_size-original_size)/1024
    print("Size difference after writing:", size_diff_kb, "KB")
    if size_diff_kb > 1024:
        print("Writing file", file_path, 'resulted in a loss of more than 1MB, halting program for safety')
        window.write_event_value(sg.WIN_CLOSED, None)


# ------------------------------------------------------------------------------
# use PIL to read data of one image
# ------------------------------------------------------------------------------
def get_img_data(file_path, rotate=0, maxsize=(800, 800), first=False) -> None:
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


if __name__ == '__main__':
    main()
