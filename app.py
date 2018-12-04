import json
import os

from flask import Flask, session, redirect, render_template, url_for, request

import browse
from indexing.whooshPowers import checkAndLoadIndex, search as _search

from power_pictures import getPowerPic
from pagination import Pagination


# template file names
home_page = "welcome_page.html"
results_page = "results.html"
power_frame = "power_div.html"

# create our flask object
app = Flask(__name__)
app.secret_key="cowcatsrock"

# change some of our flask settings
app.template_folder = os.path.join("webUI", "templates")
app.static_folder = os.path.join("webUI", "static")


@app.route('/', methods=['GET', 'POST'])
def index():
    print('HEya')
    return render_template(home_page)

@app.route('/search', methods=['GET','POST'])
def search():
    global indexr
    if request.method == 'POST':
        data = request.form
    else:
        data = request.args
    session['keywordquery'] = data.get('searchterm')
    print('Keyword Query is: ' + session['keywordquery'])
    session['search_results'] = _search(indexr, session['keywordquery'])
    return redirect('/results/')

def url_for_result_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_result_page'] = url_for_result_page

@app.route('/results/', defaults={'page': 1})
@app.route('/results/page/<int:page>')
def results(page):
    count = len(session['search_results'])
    per_page = 5
    page_results = session['search_results'][(page - 1) * per_page : (page * per_page)]
    #[0:5]

    # check if our search results are empty
    # this fix stops some exceptions, but creates an ugly page
    power_div = "Term not found."
    if (count >= 1):
        power_div = popPowerDiv(page_results[0])
    return render_template(
        results_page,
        results=page_results,
        pagination = Pagination(page,per_page,count),
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
    power_pic = getPowerPic(power_name)
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
