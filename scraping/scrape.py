import os
import sys
import time
import json
from datetime import timedelta
from urllib.request import urlopen

power_list_file = "powerData/powers_list.json"

power_data_file = "powerData/powers_data.json"
save_power_data = True

indented_power_data_file = "powerData/indented_powers_data.json"
save_indented_power_data = True

def main():
    # get a start time
    start_time = time.time()

    power_list = None
    # if the powers list does not exist, then get the list and save it
    if (os.path.isfile(power_list_file) == False):
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
        url = "http://powerlisting.wikia.com/api/v1/Articles/AsSimpleJson?id={}".format(power_id)
        # get the power json and add the power to the dictionary
        powers[power_name] = json.loads(urlopen(url).read())["sections"]
        # update the count
        count = count + 1
        # update the progress
        if (count % 10 == 0):
            percent = (count / total) * 100
            print_progress(percent)
    # update the progress to 100%
    print_progress(100.0)
    print()

    # save the dictionary as json in a more readable format
    if (save_indented_power_data == True):
        print("Writing '{}' file...".format(indented_power_data_file))
        with open(indented_power_data_file, "w") as f:
            json.dump(powers, f, indent=4)

    # save the dictionary as json
    if (save_power_data == True):
        print("Writing '{}' file...".format(power_data_file))
        with open(power_data_file, "w") as f:
            json.dump(powers, f)

    # print the overall time to run
    total_time = time.time() - start_time
    print("Done.\nTotal Time: {}\nPower Count: {}".format(timedelta(seconds=total_time), count))

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
    sys.stdout.write("\r{} {:.2f}%  ".format(pbar, percent))
    sys.stdout.flush()

if (__name__ == "__main__"):
    main()
