#!/usr/bin/python3
import requests
import json

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


class PowerNavTree(object):
    def __init__(self):
        self.cats = buildNavIndex()      
    
    def getSubcategoryOf(self, cat):
        res = []
        if cat in self.cats:
            res = self.cats.get(cat).sub_cat
        return res
    
    def getCatNav(self, cat_name):
        for cat in self.cats:
            if cat_name == cat.name:
                return cat
        return None


class PowerNav(object):
    def __init__(self, name, parent):
        self.parent = parent
        self.name = name
        self.adjacent = []
        self.sub_cat = []
        self.members = []
    
    def getMembers(self):
        self.members = []
        self.members += getCategoryMembers(self)
    
    def __repr__(self):
        cat_prefix = "Category:"
        if cat_prefix in self.name:
            return self.name[len(cat_prefix):]
        return f"{self.name}"

    def getCatPath(self):
        par = self.parent
        path = ""
        while par is not None:
            path += f"{par}-->"
            par = par.parent
        path += f"{self}"
        return path
    
    def __dict__(self):
        d = {}
        if self.parent is not None:
            d['parent'] = self.parent.name
        else:
            d['parent'] = ""
        d['sub_cat'] = []
        for sub in self.sub_cat:
            d['sub_cat'].append(sub.name)
        d['members'] = []
        for mem in self.members:
            d['members'].append(mem.name)
        return d


# class PowerEncoder(JSONEncoder):
#     def default(self, power):
#         return power.__dict__


def loadNavIndex():
    return None


def main():
    # buildTextIndex()
    buildJSONIndex()


def buildTextIndex():
    subcats = buildNavIndex()    
    members = []
    for cat in subcats:
        members += getCategoryMembers(cat)
    with open('power_cats.txt', 'w', encoding='utf-8') as file:
        for cat in subcats:
            file.write(f"{cat.getCatPath()} ({len(cat.sub_cat)} subs)" + '\n')
    file.close()

    with open('power_members.txt', 'w', encoding='utf-8') as file:
        for power in members:
            file.write(f"{power.getCatPath()}" + '\n')
    file.close()


def buildJSONIndex():
    subcats = buildNavIndex()   
    nav_dict = {}
    for cat in subcats:
        nav_dict[cat.name] = cat.__dict__()
    with open('power_cats.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(nav_dict))
    file.close()


def buildNavIndex():
    subcats = []
    all_cats = []
    unchecked = []
    for cat in categories:
        unchecked.append(PowerNav(cat, None))
    while len(unchecked) > 0:
        newcats = []
        for cat in unchecked:
            if cat.name not in all_cats:
                newcats += getSubcats(cat)
        subcats += unchecked
        unchecked = []
        for cat in newcats:
            all_cats.append(cat.name)
            unchecked.append(cat)
        print(f"{len(newcats)} new categories found")
        print(f"{len(subcats)} categories found so far ")
    print(f"scraping of categories complete; {len(subcats)} categories found")
    return subcats


def getCategoryMembers(category):
    cm_params = {
        'action': 'query',
        'list': 'categorymembers',
        'format': 'json',
        'cmlimit': 500,
        'cmtitle': category.name
    }
    print(f"getting {category}")
    cm_res = S.get(url=pl_api, params=cm_params)
    cm_json = cm_res.json()
    cmembers = []

    try:
        members = cm_json['query']['categorymembers']
        print(f"found {len(members)} members in {category}")    
        if len(members) == 500:
            print("REQUEST CAP HIT, CATEGORY TOO BIG?")
        for power in members:
            found_cat = PowerNav(power['title'], category)
            cmembers.append(found_cat)
    except KeyError:
        print(f"error while getting members of {category}")

    return cmembers


def getSubcats(category):
    subcat_params = {
        'action': 'query',
        'list': 'categorymembers',
        'format': 'json',
        'cmtype': 'subcat',
        'cmlimit': 500,
        'cmtitle': category.name
    }
    subcat_res = S.get(url=pl_api, params=subcat_params)
    subcat_json = subcat_res.json()
    subcats = []
    try:
        members = subcat_json['query']['categorymembers']
        print(f"found {len(members)} sub-categories in {category}")    
        for subcat in members:
            found_cat = PowerNav(subcat['title'], category)
            category.sub_cat.append(found_cat)
            found_cat.getMembers()
            subcats.append(found_cat)
    except KeyError:
        print(f"error while getting sub-categories of {category}")
    
    for subcat in subcats:
        print(f"{category}-->{subcat}")
    return subcats


if __name__ == '__main__':
    main()
