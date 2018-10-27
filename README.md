# cs483web-project
Group project for CS483 Web Data

## Requires Python 3

Required Modules:
...
PyQt5
whoosh
sqlite3
...

## To run:
Clone the repository.

If python 3 AND python 2 are installed, replace python with python3 below.

Navigate to the 'scraping' directory.
Execute the following command to scrape the data:
...
python scrape.py
...

Execute the following command to build the database:
...
python build_db.py
...

Navigate to the 'indexing' directory.
Execute the following command to start a terminal session:
...
python whooshPowers.py
...

Execute the following command to start a simple user interface:
...
python whooshPowers.py --gui
...

Execute the following command to show the help:
...
python whooshPowers.py --help
...
