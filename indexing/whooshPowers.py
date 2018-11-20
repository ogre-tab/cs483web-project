import csv
import ntpath
import os
import signal
import sqlite3
import sys
from io import StringIO

from whoosh.fields import ID, TEXT, Schema
from whoosh.index import Index, create_in, exists_in, open_dir
from whoosh.qparser import MultifieldParser

# TODO:
# remove the data being gathered by the search method so only the power names are returned
# update the powerdata class to check for errors and not return any nones
# pull the power data from the database instead of passing in the list of search results

# THESE ONLY WORK WHEN CALLED FROM THE ROOT DIRECTORY
db_file = os.path.join(os.getcwd(), "scraping/powerData/powers.db")
index_directory_name = os.path.join(os.getcwd(), "scraping/whooshIndex")

help_argument = "--help"
gui_argument = "--gui"


# simple class to store data about a power
class PowerData:
    def __init__(self, name, description, alias, application, capability, user, limitation):
        self.name = name
        self.description = description
        self.alias = csvStringToList(alias)
        self.application = csvStringToList(application)
        self.capability = csvStringToList(capability)
        self.user = csvStringToList(user)
        self.limitation = csvStringToList(limitation)
        self.path = name.replace(" ", "_")
        self.normalize()

    # check for any None types and set to an empty list or string
    def normalize(self):
        if (self.name is None):
            self.name = ""
        if (self.description is None):
            self.description = ""
        if (self.alias is None):
            self.alias = []
        if (self.application is None):
            self.application = []
        if (self.capability is None):
            self.capability = []
        if (self.user is None):
            self.user = []
        if (self.limitation is None):
            self.limitation = []
        if (self.path is None):
            self.path = ""

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"{self.name}: {self.description}"

#    def asDict(self):
#        d = {
#            "name": self.name,
#            "description": self.description,
#            "alias": self.alias,  # may cause problems with phrases that intentionally include quote marks...
#            "application": self.application,
#            "capability": self.capability,
#            "user": self.user,
#            "limitation": self.limitation,
#        }
#        return d


def main():
    # register signal handler for sigint
    signal.signal(signal.SIGINT, sigint_handler)

    # check arguments
    if (len(sys.argv) == 1):
        # run terminal
        startTerminal()
    # check for our gui flag
    elif (gui_argument in sys.argv):
        # try to start the gui
        try:
            # this will start our gui
            startUI()
        except Exception:
            # ask the user if they want a terminal session
            result = input("The user interface failed to load. Run in temrinal? [y/n] ")
            # if yes, start a terminal session
            if (result.lower() == "y" or result.lower() == "yes"):
                startTerminal()
            else:
                # otherwise, end the program
                return
    # check for our help flag
    elif (help_argument in sys.argv):
        printHelp()
    else:
        # anything else, print the help message
        printHelp()


def checkAndLoadIndex() -> Index:
    # check if our index directory exists
    if (os.path.isdir(index_directory_name) is False):
        try:
            # create the index directory
            os.mkdir(index_directory_name)
        except Exception as e:
            # print an error and exit
            print(f"Unable to create index directory '{index_directory_name}':\n{e}")
            sys.exit(1)
        # our index directory doesn't exist, so create our index and return it
        return createNewIndex()
    else:
        # check if our index is valid
        if (exists_in(index_directory_name) is False):
            # our index is invalid, so create our index and return it
            return createNewIndex()
        # try to load the index
        indexer = loadIndexFromDisk()
        # check if the index was loaded
        if (indexer is None):
            # build and return the index because the index didn't load
            return createNewIndex()
        elif (indexer.is_empty is True):
            # build and return the index because the index is empty
            return createNewIndex()
        else:
            # set some values for our counts that shouldn't exist
            doc_count = -100
            db_count = -10
            # get the number of documents in our index
            try:
                doc_count = indexer.doc_count()
            except Exception:
                # unable to read from the index, rebuild it
                print("Unable to read from index.")
                return createNewIndex()
            # get the number of rows in our database
            try:
                db_count = readSqlData(db_file, "SELECT COUNT(name) FROM powers")[0][0]
            except Exception:
                # if we can't read from the database, we can't build an index, so exit.
                print("Unable to read from database. Exiting.")
                sys.exit(1)
            # compare our counts
            if (doc_count == db_count):
                # the counts are the same, return our index
                return indexer
            else:
                # counts don't match, build our index and return it
                print("Index does not match database and will be built.")
                return createNewIndex()


# print how to use our program
def printHelp():
    print(f"Usage: {ntpath.basename(sys.argv[0])} [{help_argument}, {gui_argument}]")
    print(f"\t{gui_argument}: Starts a graphical interface.")
    print(f"\t{help_argument}: Prints this message.")


def startTerminal():
    # load or build our index
    indexer = checkAndLoadIndex()
    # loop forever asking the user for search terms
    runTerminal = True
    while (runTerminal is True):
        # tell the user how to stop the program and get a search term
        searchTerm = input("To exit, press ENTER with no search term.\nEnter a search term: ")
        # if the search term is blank, then stop the loop
        if (searchTerm == ""):
            runTerminal = False
        else:
            # otherwise return the search results
            search(indexer, searchTerm)


def startUI():
    # load or build our index
    indexer = checkAndLoadIndex()
    # import our gui code only when we need it
    from PyQt5.QtWidgets import QApplication
    from whooshPowersGui import WhooshGui
    # create an application
    app = QApplication(sys.argv)
    # create our window
    window = WhooshGui(indexer)
    # show our window
    window.show()
    # wait until our application ends
    app.exec_()


# handles ctrl+c (SIGINT)
# this won't work if input() is blocking while waiting for user input
def sigint_handler(sig, frame):
    try:
        # try to exit
        sys.exit(0)
    except SystemExit:
        # if that fails, force the exit
        os._exit(1)


def search(indexer, searchTerm):
    # list of tuples containing our search results
    search_results = []
    # NOTE: can add a different weighting system by adding the term to the searcher(weighting.here())
    with indexer.searcher() as searcher:
        # our attributes to search in
        columns = ["name", "description", "alias", "application", "capability", "user", "limitation"]
        # create our query
        query = MultifieldParser(columns, schema=indexer.schema).parse(searchTerm)
        # search our index with our query
        results = searcher.search(query)
        # display the results
        # print(f"====== Results for '{searchTerm}'")
        for line in results:
            # print(f"{line['name']}: {line['description']}")
            # add the name to our search results
            search_results.append(line["name"])
        # print(f"====== Total results: {str(len(results))}")
    # return the data we got from the search results
    return search_results


# convert a string with a csv format into a list
def csvStringToList(in_str: str) -> list:
    # check if the string is none
    if (in_str is None):
        return []
    # check if the string is empty
    if (in_str == ""):
        return []
    # create an in memory file
    str_io = StringIO(in_str)
    # load the file into the csv reader
    csv_r = csv.reader(str_io)
    # get a list from the reader
    csv_list = list(csv_r)
    # for some reason the list is wrapped in a list
    if (len(csv_list) > 0):
        # check if our list is empty, and return the first element
        return csv_list[0]
    else:
        # otherwise, return an empty list
        return []


# don't call this method directly, call checkAndLoadIndex() instead
def loadIndexFromDisk():
    # try to load our index from disk
    try:
        # create the schema for our index
        schema = Schema(name=TEXT(stored=True),
                        description=TEXT(stored=True),
                        alias=TEXT(stored=True),
                        application=TEXT(stored=True),
                        capability=TEXT(stored=True),
                        user=TEXT(stored=True),
                        limitation=TEXT(stored=True),
                        path=ID(unique=True))
        # load the index from our specified directory
        indexer = open_dir(index_directory_name, schema=schema)
        # return the loaded index
        print("Loaded index.")
        return indexer
    except Exception:
        # something happened while loading our index, return None
        return None


def createNewIndex():
    # create the schema for our index
    schema = Schema(name=TEXT(stored=True),
                    description=TEXT(stored=True),
                    alias=TEXT(stored=True),
                    application=TEXT(stored=True),
                    capability=TEXT(stored=True),
                    user=TEXT(stored=True),
                    limitation=TEXT(stored=True),
                    path=ID(unique=True))
    # create the index our specified directory
    print("Building index.")
    indexer = create_in(index_directory_name, schema)

    # get all the data from our database to add to the index
    print("Getting data from database...")
    columns = "name, description, alias, application, capability, user, limitation"
    powers = readSqlData(db_file, f"SELECT {columns} FROM powers")

    # add the database data to the index
    print("Indexing...")
    writer = indexer.writer()
    pad = 0
    for power in powers:
        writer.add_document(name=power[0],
                            description=power[1],
                            alias=power[2],
                            application=power[3],
                            capability=power[4],
                            user=power[5],
                            limitation=power[6],
                            path=power[0].replace(" ", "_"))
        # get the length of our power's name
        length = len(power[0]) + 1
        # update the pad length if needed
        if (length > pad):
            pad = length
        # print the current power being added
        # progress report -- UNUSED!
        # progress_check += 1
        sys.stdout.write(f"\r{power[0]}".ljust(pad))
        sys.stdout.flush()

    # commit the changes to the index
    sys.stdout.write("\rCommitting changes...".ljust(pad))
    sys.stdout.write("\n")
    sys.stdout.flush()
    writer.commit()
    # return the complete indexer
    print("Index built.")
    return indexer


# execute some sql and return true on an error
def executeSql(dbfile: str, sql: str, values=None) -> bool:
    # a place to store the connection object
    conn = None
    # did the command return an error
    result = True
    # try to execute some sql
    try:
        # connect to the database (and create the file)
        conn = sqlite3.connect(dbfile)
        # create a cursor
        cur = conn.cursor()
        # check if there are any values to use and execute the sql
        if (values is None):
            cur.execute(sql)
        else:
            cur.execute(sql, values)
        # commit the changes
        conn.commit()
        # close the database connection
        conn.close()
    except Exception as e:
        print(f"There was an error executing the SQL statement:\n{e}")
        result = False
    finally:
        # close the connection
        if (conn is not None):
            conn.close()
    # return the error value
    return result


# execute some sql and return the data as a list
def readSqlData(dbfile: str, sql: str, values=None) -> object:
    # a place to store the connection object
    conn = None
    # value returned from the sql statement
    data = None
    # try to execute some sql
    try:
        # connect to the database (and create the file)
        conn = sqlite3.connect(dbfile)
        # create a cursor
        cur = conn.cursor()
        # check if there are any values to use and execute the sql
        if (values is None):
            data = list(cur.execute(sql))
        else:
            data = list(cur.execute(sql, values))
        # close the database connection
        conn.close()
    except Exception as e:
        print(f"There was an error executing the SQL statement:\nError: {e}")
        data = None
    finally:
        # close the connection
        if (conn is not None):
            conn.close()
    # return the error value
    return data


# find index entry with this name, or error
def getPower(powername):
    # TODO:  MAKE THIS RUN FROM WHOOSH
    columns = "name, description, alias, application, capability, user, limitation"
    power = readSqlData(db_file, f"SELECT {columns} FROM powers WHERE name=?", values=[powername])
    # should only have one result from the SQL, set our power entries to the first item
    if (len(power) >= 1):
        power = power[0]
    else:
        return None

    # create the power data object and return it
    power_data = PowerData(*power)
    return power_data


if __name__ == '__main__':
    main()
