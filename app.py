import json
import os

from flask import Flask, render_template, request

import browse
from indexing.whooshPowers import checkAndLoadIndex, search

default_power_pic = "https://allinonebusiness-services.co.uk/wp-content/uploads/2015/11/hero-small.png"

# template file names
home_page = "welcome_page.html"
results_page = "results.html"
power_frame = "power_div.html"

# create our flask object
app = Flask(__name__)
# change some of our flask settings
app.template_folder = os.path.join("webUI", "templates")
app.static_folder = os.path.join("webUI", "static")


@app.route('/', methods=['GET', 'POST'])
def index():
    print('HEya')
    return render_template(home_page)


@app.route('/results/', methods=['GET', 'POST'])
def results():
    global indexr
    if request.method == 'POST':
        data = request.form
    else:
        data = request.args
    keywordquery = data.get('searchterm')
    print('Keyword Query is: ' + keywordquery)
    search_results = search(indexr, keywordquery)

    # check if our search results are empty
    # this fix stops some exceptions, but creates an ugly page
    power_div = "Term not found."
    if (len(search_results) >= 1):
        power_div = popPowerDiv(search_results[0])
    return render_template(
        results_page, 
        query=keywordquery, 
        results=search_results, 
        power_view=power_div)


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
    power_data = browse.getPowerData(power_name)
    power_pic = default_power_pic
    # if powerdata has image link, put it here
    power_div = render_template(
        power_frame, 
        power=power_data, 
        power_pic=power_pic)
    return power_div


@app.route('/results/data/<power>')
def getPowerData(power):
    json_power = json.dumps(browse.getPowerData(power))
    return json_power


if __name__ == '__main__':
    global indexr

    indexr = checkAndLoadIndex()
    app.run(debug=True)
