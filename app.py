import json
import os

from flask import Flask, render_template, request

# browse currently unused
# import browse
from indexing.whooshPowers import PowerIndex
from scraping.power_pictures import getPowerPic
from scraping.power_pictures import linkScraping

from scraping.navData.catscraping import readJSONIndex

# template file names
home_page = "welcome_page.html"
results_page = "results.html"
power_frame = "power_div.html"
power_frame_null = "empty_power_div.html"
results_frame = "results_div.html"

results_per_page = 10

# create our flask object
app = Flask(__name__)

# change some of our flask settings
app.template_folder = os.path.join("webUI", "templates")
app.static_folder = os.path.join("webUI", "static")

# create our power index
powerIndex = PowerIndex()

""" API Arguments:
        # term to request search results
        keywordquery = terms.get('query')

        # page number (from 1) to display of results
        page_num = terms.get('p')

        # exact pathname to Power
        power_path = terms.get('power')

        # exact pathname to Category
        getCategory = terms.get('category')

        get a particular fragment of a HTML.  Returns full page if left blank
        div = terms.get('div')
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    # Render Main Landing Page
    print('HEya')
    return render_template(home_page)


@app.route('/search', methods=['GET', 'POST'])
def results():
    # function which returns requests to the 'search' route
    if request.method == 'POST':
        terms = request.form
    else:
        terms = request.args
    print(terms)
    keywordquery = terms.get('query')
    page_num = terms.get('p')
    if page_num is None:
        page_num = 1
    power_path = terms.get('power')
    div = terms.get('div')

    if power_path is not None:
        if div == 'pow':
            if terms.get('format') == 'json':
                return getPowerDataJSON(power_path)
            return popPowerDiv(power_path)
        if div == 'pic':
            return getPowerPic(power_path)

    if div == 'res':
        if terms.get('format') == 'json':
            return json.dumps(getSearchResults(keywordquery))
        return popResultsDiv(keywordquery, page_num)

    # default option
    return loadBrowsingPage(terms)


def loadBrowsingPage(terms):
    # returns pre-filled HTML page with javascript application
    keywordquery = terms.get('query')
    print(f'Keyword Query is: {keywordquery}')
    search_results = getSearchResults(keywordquery)

    first_power = ""
    # check if our search results are empty
    if len(search_results) > 0:
        first_power = search_results[0]
    return render_template(
        results_page,
        query=keywordquery,
        results=search_results,
        power_name=first_power,
        this_query=keywordquery,
        results_view=popResultsDiv(keywordquery, 0),
        results_list=json.dumps(search_results))


def popPowerDiv(power_name):
    # Returns HTML for the "power-view" div of the browsing page
    power_data = powerIndex.getPower(power_name)
    if power_data is None:
        return render_template(power_frame_null)
        # return f"Invalid Power Page: {power_name}"

    power_pic = getPowerPic(power_name)
    # if powerdata has image link, put it here

    # Default values for empty fields
    if len(power_data.description) == 0:
        power_data.description = "No Description Available"
    if len(power_data.alias) == 0:
        power_data.alias = ["(No Aliases for " + power_data.name + ")"]
    if len(power_data.application) == 0:
        power_data.application = ["No known Limitations or Counter-Abilities"]
    if len(power_data.capability) == 0:
        power_data.capability = ["Capabilities of this power are unknown."]
    if len(power_data.user) == 0:
        power_data.user = ["No Known Users"]
    if len(power_data.limitation) == 0:
        power_data.limitation = ["No known Limitations or Counter-Abilities"]

    power_div = render_template(
        power_frame,
        power=power_data,
        power_pic=power_pic)
    return power_div


def getPowerDataJSON(power_name):
    # returns PowerData schema as JSON
    power_data = powerIndex.getPower(power_name)
    if power_data is not None:
        d = power_data.asDict()
        print(d)
        return json.dumps(d)
    else:
        return f"Invalid Power Page: {power_name}"


def getSearchResults(keywordquery):
    # Returns list of search results
    print('Keyword Query is: ' + keywordquery)
    results = []

    # Get the normal whoosh results
    whooshy = powerIndex.search(keywordquery)

    # check for an exact title match first
    exact = powerIndex.getTitleMatch(keywordquery)
    if exact is not None:
        results.append(exact)
        # remove duplicate entry if it exists
        if exact in whooshy:
            whooshy.remove(exact)

    results += whooshy
    return results


@app.route('/ps/<power_name>')
def linkScrape(power_name):
    # Experimental Link-scraping function
    return linkScraping(power_name)


@app.route('/category/<category_name>')
def getSubcategoriesJSON(category_name):
    # experimental function to get subcategories
    categories = readJSONIndex()
    if category_name == "all":
        return json.dumps(categories)
    return json.dumps(categories[category_name])


def popResultsDiv(keywordquery, page_num):
    # DEPRICATED: returns HTML page-div with results
    print(page_num)
    page_num = int(page_num)
    if page_num <= 0:
        page_num = 1
    results_list = getSearchResults(keywordquery)
    total_count = len(results_list)
    last_page = (int)(total_count / results_per_page)
    if (total_count % results_per_page > 0):
        last_page += 1

    if (page_num > last_page):
        page_num = last_page

    page_start = (page_num - 1) * results_per_page
    page_end = min(total_count, page_start + results_per_page)
    results_list = results_list[page_start:page_end]

    pages = []
    if page_num > 1:
        pages.append("<")
    for i in range(0, last_page):
        if i == page_num - 1:
            pages.append(f"[{i+1}]")
        else:
            pages.append(f"{i+1}")
    if page_num < last_page:
        pages.append(">")

    return render_template(
        results_frame,
        this_query=keywordquery,
        results=results_list,
        page_nums=pages,
        results_range=f"{page_start+1}-{page_end} of {total_count}")


if __name__ == '__main__':
    app.run(debug=True)
