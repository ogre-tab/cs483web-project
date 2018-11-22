#!/usr/bin/python3
import os
import sys
import json
import requests

S = requests.Session()
"""
scraping
http://powerlisting.wikia.com/api.php?action=query&prop=revisions&titles=100%25_Muscle_Usage&prop=revisions&rvprop=content

api page:
http://powerlisting.wikia.com/api.php

categrory listing:
http://powerlisting.wikia.com/api/v1/Navigation/Data

subcat listing:
http://powerlisting.wikia.com/api.php?action=query&list=categorymembers&format=json&cmtype=subcat&cmlimit=500&cmtitle=Category:Enhancements

"""

pl_api = "http://powerlisting.wikia.com/api.php"

categories = [
    'Category:Enhancements',
    'Category:Mental_Powers',
    'Category:Personal_Physical_Powers',
    'Category:Mimicry',
    'Category:Manipulations',
    'Category:Almighty_Powers'
    ]


def main():
    subcats_1 = []
    for cat in categories:
        subcats_1.append(getSubcats(cat))
    subcats_2 = []
    for subcat in subcats_1:
        subcats_2.append(getSubcats(subcat))
    with open('power_cats.txt', 'w', encoding='utf-8') as file:
        for cat in categories:
            file.write(cat + '\n')
        for cat in subcats_1:
            file.write(cat + '\n')
        for cat in subcats_2:
            file.write(cat + '\n')
    file.close()


def getCategoryMembers(category):
    cm_params = {
        'action': 'query',
        'list': 'categorymembers',
        'format': 'json',
        'cmlimit': 500,
        'cmtitle': f"Category:{category}"
    }
    print(f"getting {category}")
    cm_res = S.get(url=pl_api, params=cm_params)
    cm_json = cm_res.json()
    cmembers = []
    print(cm_json)
    members = cm_json['query']['categorymembers']
    for power in members:
        cmembers.append(power['title'])
    return cmembers


def getSubcats(category):
    subcat_params = {
        'action': 'query',
        'list': 'categorymembers',
        'format': 'json',
        'cmtype': 'subcat',
        'cmlimit': 500,
        'cmtitle': category
    }
    print(f"getting {category}")
    subcat_res = S.get(url=pl_api, params=subcat_params)
    subcat_json = subcat_res.json()
    subcats = []
    print(subcat_json)
    members = subcat_json['query']['categorymembers']
    for subcat in members:
        subcats.append(subcat['title'])
    return subcats


if __name__ == '__main__':
    main()
