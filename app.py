import os
from flask import Flask, render_template, request
from flask import jsonify

from indexing.whooshPowers import checkAndLoadIndex, search

import browse

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


@app.route('/my-link/')
def my_link():
    print('clicked')
    return 'Click'


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
        power_div = render_template(power_frame, power=search_results[0])
    return render_template(results_page, query=keywordquery, results=search_results, power_view=power_div)


@app.route('/results/power/<power_name>')
def pop_result(power_name):
    power_data = browse.getPowerData(power_name)
    power_div = render_template(power_frame, power=power_data)
    return power_div


@app.route('/power/<page>')
def power_page(page):
    print(f'Loading info for "{page}""')
    
    power_data = browse.getPowerData(page)
    power_div = render_template(power_frame, power=power_data)
    return render_template(results_page, query="", results=[page], power_view=power_div) 


@app.route('/results/data/<power>')
def getPowerData(power):
    pow = browse.getPowerData(power).asDict()
    return jsonify(pow)


if __name__ == '__main__':
    global indexr

    indexr = checkAndLoadIndex()
    app.run(debug=True)
