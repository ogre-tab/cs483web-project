import json
import os
import sys
import time
from datetime import timedelta
from urllib.request import urlopen

# folder names
data_folder_name = "powerData"
scrape_folder_name = "scraping"

# file names
power_list_file_name = "powers_list.json"
power_data_file_name = "powers_data.json"
indented_power_data_file_name = "indented_powers_data.json"

# create optional files
create_indented_power_data = False


def main():
    # get a start time
    start_time = time.time()

    # get our file paths
    files = get_paths()

    # get our files and paths from the files dictionary
    data_folder = files[data_folder_name]
    power_list_file = files[power_list_file_name]
    power_data_file = files[power_data_file_name]
    indented_power_data_file = files[indented_power_data_file_name]

    # check that our data folder exists
    if (os.path.isdir(data_folder) is False):
        # try to create the directory
        try:
            os.mkdir(data_folder)
        except Exception as e:
            # if unable to create the directory, tell the user and exit
            print(f"Unable to make data directory.\n{e}")
            sys.exit(1)

    power_list = None
    # if the powers list does not exist, then get the list and save it
    if (os.path.isfile(power_list_file) is False):
        print("Getting list of powers...")
        json_data = urlopen("http://powerlisting.wikia.com/api/v1/Articles/List?category=Powers&limit=15000").read()
        # load the powers list from the json data
        power_list = json.loads(json_data.decode("utf-8"))
        # save the powers list from the json data
        with open(power_list_file, "wb") as f:
            f.write(json_data)
    else:
        # load the powers list from the json file
        with open(power_list_file, "r") as f:
            power_list = json.load(f)

    # create a dictionary to store the powers
    powers = dict()

    # read each power and save to the dictionary
    print("Getting all power data...")
    total = len(power_list["items"])
    count = 0
    for item in power_list["items"]:
        # get our power id and title
        power_id = item["id"]
        power_name = item["title"]
        # create our url to pull data from
        url = f"http://powerlisting.wikia.com/api/v1/Articles/AsSimpleJson?id={power_id}"
        # get the power json and add the power to the dictionary
        powers[power_name] = json.loads(urlopen(url).read().decode("utf-8"))["sections"]
        # update the count
        count = count + 1
        # update the progress
        if (count % 10 == 0):
            percent = (count / total) * 100
            print_progress(percent)
    # update the progress to 100%
    print_progress(100.0)
    print()

    # save the dictionary as json
    print(f"Writing '{power_data_file}' file...")
    with open(power_data_file, "w") as f:
        json.dump(powers, f)

    # save the dictionary as json in a more readable format
    if (create_indented_power_data is True):
        print(f"Writing '{indented_power_data_file}' file...")
        with open(indented_power_data_file, "w") as f:
            json.dump(powers, f, indent=4)

    # print the overall time to run
    total_time = time.time() - start_time
    print(f"Done.\nTotal Time: {timedelta(seconds=total_time)}\nPower Count: {count}")


# get our file names and folder paths
def get_paths() -> dict:
    # file paths will get stored in a dictionary
    fileDict = {}
    # get our working folder
    cwd = os.getcwd()
    # get the base folder of our working folder
    base = os.path.basename(os.path.normpath(cwd))
    # check if our base is our target folder
    if (base == scrape_folder_name):
        # since our base is our target folder, create the paths without the base added
        fileDict[power_list_file_name] = os.path.join(cwd, data_folder_name, power_list_file_name)
        fileDict[power_data_file_name] = os.path.join(cwd, data_folder_name, power_data_file_name)
        fileDict[indented_power_data_file_name] = os.path.join(cwd, data_folder_name, indented_power_data_file_name)
        fileDict[data_folder_name] = os.path.join(cwd, data_folder_name)
    else:
        # since our base is NOT our target folder, create the paths WITH the base added
        fileDict[power_list_file_name] = os.path.join(cwd, scrape_folder_name, data_folder_name, power_list_file_name)
        fileDict[power_data_file_name] = os.path.join(cwd, scrape_folder_name, data_folder_name, power_data_file_name)
        fileDict[indented_power_data_file_name] = os.path.join(cwd, scrape_folder_name, data_folder_name, indented_power_data_file_name)
        fileDict[data_folder_name] = os.path.join(cwd, scrape_folder_name, data_folder_name)
    # return our file paths
    return fileDict


# create a text progress bar
def print_progress(percent: float):
    # the number of bars to write
    bars = 50
    pendr = "|"
    pendl = "|"
    pchar = "█"
    nchar = "░"
    # the percentage each bar represents
    chunk = int(100 / bars)
    # the number of filled bars
    barcount = int(percent / chunk)
    # put all the peices together
    pbar = pendl + (barcount * pchar) + ((bars - barcount) * nchar) + pendr
    # output the progress bar
    sys.stdout.write(f"\r{pbar} {percent:.2f}%  ")
    sys.stdout.flush()


if (__name__ == "__main__"):
    main()
