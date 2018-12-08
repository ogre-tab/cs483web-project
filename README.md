# cs483web-project
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

### To run:
	Clone the repository.
		https://github.com/ogre-tab/cs483web-project.git
	
	Build the Database:
		run scraping/scrape.py
		run scraping/build_db.py
	Note: The database, powers.db, will be in scraping/powerData.
	
	Run 'app.py' to start the flask webserver.
		The program will start and build the whoosh index on start up.
	
	Navigate to the page provided by a link in the terminal.
