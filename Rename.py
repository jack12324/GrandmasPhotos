import os


def rename_photos(search, replace):
    lfiles = os.listdir()
    for file in lfiles:
        if search in file:
            if os.path.isfile(file):
                split = file.split("_")
                new_name = replace+"_"+split[1]
                os.rename(file, new_name)

def increase_index(search, base):
    lfiles = os.listdir()
    for file in lfiles:
        if search in file:
            if os.path.isfile(file):
                year_and_index = file.split("_")
                index_and_file = year_and_index[1].split(".")
                num = int(index_and_file[0]) + base
                new_name = "temp-"+year_and_index[0]+"_"+str(num)+"."+index_and_file[1]
                os.rename(file, new_name)
                f.write(new_name)
                f.write("\n")
    lfiles = os.listdir()
    for file in lfiles:
        print(file)
        if search in file:
            print(file)
            if os.path.isfile(file):
                print(file)
                remove_temp = file.split("-")
                os.rename(file, remove_temp[1])


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    rename_photos("10s", "2010s")
