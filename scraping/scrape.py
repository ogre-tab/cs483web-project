import bs4
import os
import sys
import time
from datetime import timedelta
from urllib.request import urlopen

def main():
    import json
    # get a start time
    start_time = time.time()

    # if the powers list does not exist, then get the list and save it
    if (os.path.exists("allpowers.json") == False):
        print("Getting list of powers...")
        json = urlopen("http://powerlisting.wikia.com/api/v1/Articles/List?category=Powers&limit=15000").read()
        with open("allpowers.json", "wb") as f:
            f.write(json)

    # load the powers list from the json file
    with open("allpowers.json", "r") as f:
        data = json.load(f)

    # create a dictionary to store the read powers
    powers = dict()

    # read each power and save to the dictionary
    print("Getting all power data...")
    total = len(data["items"])
    count = 0
    for item in data["items"]:
        # get our power id and title
        power_id = item["id"]
        power_name = item["title"]
        # DEBUG: print the power that is being saved
        #print(power_name)
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

    # save the dictionary as json as a more readable format
    print("\nWriting files...")
    with open("powerdatapretty.json", "w") as f:
        json.dump(powers, f, indent=4)

    # save the dictionary as json
    with open("powerdata.json", "w") as f:
        json.dump(powers, f)

    # print the overall time to run
    total_time = time.time() - start_time
    print("Done.\nTotal Time: {}".format(timedelta(seconds=total_time)))

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
