import ntpath
import os
import signal
import sqlite3
import sys

from PyQt5.QtWidgets import QApplication
from whoosh.fields import ID, TEXT, Schema
from whoosh.index import Index, create_in, exists_in, open_dir
from whoosh.qparser import MultifieldParser

db_file = "../scraping/powerData/powers.db"
index_directory_name = "whooshIndex"

help_argument = "--help"
gui_argument = "--gui"

# TODO:
# clean up gui


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
                sys.exit(10)
    # check for our help flag
    elif (help_argument in sys.argv):
        printHelp()
    else:
        # anything else, print the help message
        printHelp()


def checkIndex() -> Index:
    # check if our index directory exists
    if (os.path.isdir(index_directory_name) is False):
        try:
            # create the index directory
            os.mkdir(index_directory_name)
        except Exception as e:
            # print an error and exit
            print("Unable to create index directory '{}':\n{}".format(index_directory_name, e))
            sys.exit(1)
        # our index directory doesn't exist, so create our index and return it
        return createNewIndex()
    else:
        # check if our index is valid
        if (exists_in(index_directory_name) is False):
            # our index is invalid, so create our index and return it
            return createNewIndex()
        # try to load the index
        indexer = loadIndex()
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
                # counts differ, build our index and return it
                print("Index is incomplete and needs to be built.")
                return createNewIndex()


# print how to use our program
def printHelp():
    print("Usage: {} [{}, {}]".format(ntpath.basename(sys.argv[0]), help_argument, gui_argument))
    print("\t{}: Starts a graphical interface.".format(gui_argument))
    print("\t{}: Prints this message.".format(help_argument))


def startTerminal():
    # load or build our index
    indexer = checkIndex()
    # tell the user how to stop the program
    print("To exit, press ENTER with no search term.")
    # loop forever asking the user for search terms
    runTerminal = True
    while (runTerminal is True):
        searchTerm = input("Enter a search term: ")
        # if the search term is blank, then stop the loop
        if (searchTerm == ""):
            runTerminal = False
        else:
            # otherwise return the search results
            search(indexer, searchTerm)


def startUI():
    # load or build our index
    indexer = checkIndex()
    # import our gui code only when we need it
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
def sigint_handler(sig, frame):
    try:
        # try to exit
        sys.exit(0)
    except SystemExit:
        # if that fails, force the exit
        os._exit(1)


def search(indexer, searchTerm):
    # NOTE: can add a different weighting system by adding the term to the searcher(weighting.here())
    with indexer.searcher() as searcher:
        # create our query
        query = MultifieldParser(["name", "description"], schema=indexer.schema).parse(searchTerm)
        # search our index with our query
        results = searcher.search(query)
        # display the results
        print("\n====== Results for '{}'\n".format(searchTerm))
        for line in results:
            print("{}:\n{}\n".format(line["name"], line["description"]))
        print("====== Total results: " + str(len(results)))


def loadIndex():
    # try to load our index
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
    powers = readSqlData(db_file, "SELECT {} FROM powers".format(columns))

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
        sys.stdout.write("\r{}".format(power[0]).ljust(pad))
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
        print("There was an error executing the SQL statement:\n{}".format(e))
        result = False
    finally:
        # close the connection
        if (conn is not None):
            conn.close()
    # return the error value
    return result


# execute some sql and return the data
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
        print("There was an error executing the SQL statement:\nError: {}".format(e))
        data = None
    finally:
        # close the connection
        if (conn is not None):
            conn.close()
    # return the error value
    return data


if __name__ == '__main__':
    main()
