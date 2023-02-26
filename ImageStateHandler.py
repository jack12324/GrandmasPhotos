import io
import os

from PIL import Image, ImageTk

import ImageStateLoader
from ImageState import ImageState
from UploadHandler import UploadHandler


class ImageStateHandler:

    def __init__(self, folder: str, upload_handler: UploadHandler):
        self.upload_handler = upload_handler
        self.file_states = ImageStateLoader.load_image_states()
        self.all_tifs = self.__get_all_tif_files(folder)
        self.previous_queue = []
        self.convert_queue = []
        self.upload_queue = []
        self.rotate_queue = []
        self.__sort_tifs()

    # returns array of path to all tif files in a given directory
    # also searches subdirectories
    def __get_all_tif_files(self, start_path: str) -> [str]:
        tif_files = []
        lfiles = os.listdir(start_path)
        for file in lfiles:
            file_path = os.path.join(start_path, file)
            if os.path.isfile(file_path):
                if file.endswith(".tif"):
                    tif_files.append(file_path)
            else:
                tif_files.extend(self.__get_all_tif_files(file_path))
        return tif_files

    def __convert_image(self, image_path: str) -> None:
        # importing the image
        filename = image_path.replace("Tif", "Jpg")
        filename = filename.replace("tif", "jpg")
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        im = Image.open(image_path)
        # converting to jpg
        rgb_im = im.convert("RGB")
        # exporting the image
        rgb_im.save(filename, quality=95)

    def convert_all_rotated(self) -> None:
        while len(self.convert_queue) > 0:
            image = self.convert_queue.pop()
            self.__convert_image(image)
            self.file_states[image].converted = True
            if image not in self.upload_queue:
                self.upload_queue.append(image)
        ImageStateLoader.save_image_states(self.file_states)

    def __sort_tifs(self) -> None:
        for tif in self.all_tifs:
            if tif in self.file_states:
                if self.file_states[tif].rotated:
                    if self.file_states[tif].converted:
                        if self.file_states[tif].uploaded:
                            continue
                        else:
                            self.upload_queue.append(tif)
                    else:
                        self.convert_queue.append(tif)
                else:
                    self.rotate_queue.append(tif)
            else:
                self.file_states[tif] = ImageState()
                self.rotate_queue.append(tif)

    def image_rotated(self, filename: str) -> None:
        self.file_states[filename].rotated = True
        self.file_states[filename].converted = False
        self.file_states[filename].uploaded = False
        if filename not in self.convert_queue:
            self.convert_queue.append(filename)
        if filename in self.upload_queue:
            self.upload_queue.remove(filename)
        self.previous_queue.append(filename)
        self.rotate_queue.remove(filename)

    def save_image_states(self) -> None:
        ImageStateLoader.save_image_states(self.file_states)

    def get_num_to_upload(self) -> int:
        return len(self.upload_queue)

    def get_num_to_convert(self) -> int:
        return len(self.convert_queue)

    def get_num_to_rotate(self) -> int:
        return len(self.rotate_queue)

    def get_display_image(self) -> str:
        if len(self.rotate_queue) == 0:
            return "default_image.jpg"
        else:
            return self.rotate_queue[0]

    def reset_previous(self) -> None:
        self.rotate_queue.insert(0, self.previous_queue.pop())
        filename = self.rotate_queue[0]
        self.file_states[filename].rotated = False
        self.file_states[filename].converted = False
        self.file_states[filename].uploaded = False
        if filename in self.convert_queue:
            self.convert_queue.remove(filename)
        if filename in self.upload_queue:
            self.upload_queue.remove(filename)

    def __upload_complete(self, filename: str) -> None:
        self.file_states[filename].uploaded = True
        if filename in self.convert_queue:
            self.convert_queue.remove(filename)
        if filename in self.upload_queue:
            self.upload_queue.remove(filename)

    def get_file_state(self, filename: str) -> ImageState:
        return self.file_states[filename]

    def get_num_rotated(self) -> int:
        return len(self.previous_queue)

    def upload_all_converted(self):
        self.upload_handler.upload_image(self.upload_queue[0])
        self.__upload_complete(self.upload_queue[0])
