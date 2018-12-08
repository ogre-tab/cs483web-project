Super Power Super-Search

Project for CS483 Web Data by Super Search Team

Requires Python 3
Requires Internet Access

Required Python Modules:
* flask
* requests
* sqlite3
* whoosh

Compatible Web Browsers:
* Chrome
* Firefox

To run:
	Clone the repository.
		https://github.com/ogre-tab/cs483web-project.git
	
	If the database file scraping/powerData/powers.db does not exist.
	Then, scrape and build the database:
		1. run 'python scraping/scrape.py'
		2. run 'python scraping/build_db.py'
	
	Run 'python app.py' to start the flask webserver.
		The program will start and build the whoosh index on start up.
		If the index already exists, it will be loaded.
	
	Navigate to the page provided by a link in the terminal.
	Default url: http://127.0.0.1:5000

	Note: If python2 and python3 are installed, use the python3
	binary to start all scripts.
