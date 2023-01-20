# importing the module
from PIL import Image
import progressbar
import os


def convert_image(image_path):
    # importing the image
    filename = image_path.replace("Tif", "Jpg")
    filename = filename.replace("tif", "jpg")
    if not os.path.isfile(filename):
        im = Image.open(image_path)
        # converting to jpg
        rgb_im = im.convert("RGB")
        # exporting the image
        rgb_im.save(filename, quality=95)
        return 1
    else:
        return 0


def rename_photos_at_path(path, progress_bar):
    ignore = ['.idea', 'env', 'main.py', 'Jpg']
    lfiles = os.listdir(path)
    total_done = 0
    for file in lfiles:
        if file not in ignore:
            file_path = f'{path}\\{file}'
            if os.path.isfile(file_path):
                total_done += convert_image(file_path)
                progress_bar.update(total_done)
            else:
                new_path = file_path.replace("Tif", "Jpg")
                if not os.path.exists(new_path):
                    os.mkdir(new_path)
                total_done = rename_photos_at_path(file_path, progress_bar)
                progress_bar.update(total_done)
    return total_done

#t
def get_total_files(path):
    ignore = ['.idea', 'env', 'main.py', 'Jpg']
    lfiles = os.listdir(path)
    total = 0
    for file in lfiles:
        if file not in ignore:
            file_path = f'{path}\\{file}'
            if os.path.isfile(file_path):
                if not jpg_exists_for_tif(file_path):
                    total += 1
            else:
                total += get_total_files(file_path)
    return total


def jpg_exists_for_tif(file_path):
    jpg_file_path = file_path.replace("Tif", "Jpg").replace("tif", "jpg")
    return os.path.isfile(jpg_file_path)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    total = get_total_files('Photos')
    bar = progressbar.ProgressBar(maxval=total).start()
    done = rename_photos_at_path('Photos', bar)
    bar.update(done)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
