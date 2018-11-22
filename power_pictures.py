#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup

default_power_pic = "https://allinonebusiness-services.co.uk/wp-content/uploads/2015/11/hero-small.png"


# adapted from pierson's image getter function
def getPowerPic(page_name):
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