import os

from flask import Flask, render_template, request

from indexing.whooshPowers import checkAndLoadIndex, search

# template file names
home_page = "welcome_page.html"
results_page = "results.html"

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

    return render_template(results_page, query=keywordquery, results=search_results)


if __name__ == '__main__':
    global indexr

    indexr = checkAndLoadIndex()
    app.run(debug=True)
