from flask import Flask, render_template, url_for, request
import sys
sys.path.append("../")
import indexing.whooshPowers as wp

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
	print('HEya')
	return render_template('welcome_page.html')

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
	test = data.get('test')

	print('Keyword Query is: ' + keywordquery)
	print('Test Query is: ' + test)

	name, description = wp.search(indexr, keywordquery)
	
	return render_template('results.html', query=keywordquery, results=zip(name, description))



if __name__ == '__main__':
	global indexr
	indexr = wp.loadIndex()
	app.run(debug=True)
