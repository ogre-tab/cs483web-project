import bs4
from urllib.request import urlopen #, urlretrieve
#from urllib.parse import unquote

# the root of the site
root_url = "http://powerlisting.wikia.com"

# use the power list url as the base to get other urls from
start_url = "/wiki/Category:Powers"

# a place to store the power urls found so we can parse them later
urls = set()
# the starting url
next_url = "{}{}".format(root_url, start_url)
while (next_url != None):
    # DEBUG print the url being worked on
    print(next_url)
    # get the page source
    html = urlopen(next_url).read()
    # create a soup object from the html
    soup = bs4.BeautifulSoup(html, features="html.parser")
    # look for links in the tables
    tables = soup.findChildren("table")
    # only look through the second table for <a> tags
    for ref in tables[1].findChildren("a", href=True):
        # get the url from the tag
        power_url = ref["href"]
        # check that the url is not a category url
        #if ("Category:" not in power_url):
        # add the url our set of urls
        urls.add("{}{}".format(root_url, power_url))
    # get the next page <a> tag
    next_page = soup.find("a", href=True, text="next 200")
    # get the url from the tag if the tag was found
    if (next_page == None):
        next_url = None
    else:
        next_url = "{}{}".format(root_url, next_page["href"])

# DEBUG: sort the urls set
sorted_list = sorted(urls)
# DEBUG: write the urls to file
with open("powers.txt", "w") as f:
    # DEBUG: print the urls
    for url in sorted_list:
        f.write("{}\n".format(url))
        print(url)
# DEBUG: print the url count
print("url count: {}".format(len(urls)))
