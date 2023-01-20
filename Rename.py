import os


def rename_photos(search, replace):
    lfiles = os.listdir()
    for file in lfiles:
        if search in file:
            if os.path.isfile(file):
                split = file.split("_")
                new_name = replace+"_"+split[1]
                os.rename(file, new_name)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    rename_photos("90s", "1990s")
