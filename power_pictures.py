#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup

default_power_pic = "https://allinonebusiness-services.co.uk/wp-content/uploads/2015/11/hero-small.png"
# pic_request = f"http://powerlisting.wikia.com/api.php?action=imageserving&format=json&wisTitle={page_name}"


# adapted from pierson's image-getter function
def scrapePowerPic(page_name):
    url = f"http://powerlisting.wikia.com/wiki/{page_name}"
    req = requests.get(url)
    
    # get the page content
    soup = BeautifulSoup(req.content, "lxml") 
    x = list()
    for links in soup.find_all('img'):
        # print(links.get('src'))
        x.append(links.get('src'))
        # DEBUG
    
    power_pic = default_power_pic
    if len(x) >= 2:
        power_pic = x[1] 
    return power_pic


# straight-up API request, returns image url
def getPowerPic(page_name):
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
