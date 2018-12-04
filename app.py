import json
import os

from flask import Flask, render_template, request

# browse currently unused
# import browse
from indexing.whooshPowers import PowerIndex
from power_pictures import getPowerPic

# template file names
home_page = "welcome_page.html"
results_page = "results.html"
power_frame = "power_div.html"
results_frame = "results_div.html"

results_per_page = 10

# create our flask object
app = Flask(__name__)

# change some of our flask settings
app.template_folder = os.path.join("webUI", "templates")
app.static_folder = os.path.join("webUI", "static")

# create our power index
powerIndex = PowerIndex()


@app.route('/', methods=['GET', 'POST'])
def index():
    print('HEya')
    return render_template(home_page)


@app.route('/results/', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        data = request.form
    else:
        data = request.args
    keywordquery = data.get('searchterm')
    print('Keyword Query is: ' + keywordquery)
    search_results = getSearchResults(keywordquery)

    first_power = ""
    # check if our search results are empty
    if len(search_results) > 0:
        first_power = search_results[0]
        
    return render_template(
        results_page,
        query=keywordquery,
        results=search_results,
        power_view=popPowerDiv(first_power),
        this_query=keywordquery,
        results_view=popResultsDiv(keywordquery, 0),
        results_list=json.dumps(search_results))


@app.route('/results/power/<power_name>')
def pop_result(power_name):
    return popPowerDiv(power_name)


@app.route('/power/<page>')
def power_page(page):
    print(f"Loading info for '{page}'")
    return render_template(
        results_page, query="",
        # adjacent powers?
        results=[page],
        power_view=popPowerDiv(page))


def popPowerDiv(power_name):
    power_data = powerIndex.getPower(power_name)
    if power_data is None:
        return f"Invalid Power Page: {power_name}" 

    power_pic = getPowerPic(power_name)
    # if powerdata has image link, put it here

    power_div = render_template(
        power_frame,
        power=power_data,
        power_pic=power_pic)
    return power_div


@app.route('/results/data/<power_name>')
def getPowerData(power_name):
    power_data = powerIndex.getPower(power_name)
    if power_data is not None:
        return json.dumps(power_data)
    else:
        return f"Invalid Power Page: {power_name}" 


def getSearchResults(keywordquery):
    # Returns list of search results
    print('Keyword Query is: ' + keywordquery)
    search_results = powerIndex.search(keywordquery)
    # Do we need to check for no-list?
    return search_results


@app.route('/results/list/<keywordquery>')
def getSearchResultsJSON(keywordquery):
    return json.dumps(getSearchResults(keywordquery))


@app.route('/results/list/p<page_num>/<keywordquery>')
def popResultsDiv(keywordquery, page_num):
    # returns page within results
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
    
    page_start = (page_num -1) * results_per_page
    page_end = min(total_count, page_start + results_per_page)
    results_list = results_list[page_start:page_end]
    
    pages = [] 
    if page_num > 1:
        pages.append("<")
    for i in range(0, last_page):
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
