#!/usr/bin/python3
import requests

default_power_pic = "https://allinonebusiness-services.co.uk/wp-content/uploads/2015/11/hero-small.png"
# pic_request = f"http://powerlisting.wikia.com/api.php?action=imageserving&format=json&wisTitle={page_name}"


def getPowerPic(page_name):
    # straight-up API request, returns image url
    power_pic = default_power_pic
    pl_api = "http://powerlisting.wikia.com/api.php"
    pic_params = {
        'action': 'imageserving',
        'format': 'json',
        'wisTitle': page_name
    }
    S = requests.Session()
    print(f"getting image for {page_name}")
    pic_res = S.get(url=pl_api, params=pic_params)
    pic_json = pic_res.json()
    print(pic_json)
    try:
        power_pic = pic_json["image"]["imageserving"]
        print("found" + power_pic)
    except KeyError:
        print(f"no pic found for {page_name}, using default")
    return power_pic


def linkScraping(power_name):
    # Experimental link-scraping function
    pl_api = "http://powerlisting.wikia.com/api.php"
    params = {
        'action': 'query',
        'prop': 'revisions',
        'rvprop': 'content',
        'titles': power_name
    }
    links = ""
    S = requests.Session()
    print(f"getting links for {params}")
    links_raw = S.get(url=pl_api, params=params)
    return links_raw.text