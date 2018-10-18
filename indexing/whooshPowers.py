import os
import sys
import sqlite3
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser, MultifieldParser

db_file = "../scraping/powerData/powers.db"
index_directory_name = "whooshIndex"

def main():
    searchTerm = "Strength"
    indexer = createNewIndex()
    #results = search(indexer, searchTerm)
    search(indexer, searchTerm)

# check ifour index directory exists
def checkForIndexDirectory():
    try:
        # if the directory is not found, then create the directory
        if (os.path.isdir(index_directory_name) == False):
            os.mkdir(index_directory_name)
    except Exception as e:
        # print an error and exit
        print("Unable to create index directory '{}':\n{}".format(index_directory_name, e))
        sys.exit(1)

def search(indexer, searchTerm):
    # NOTE: can add a different weighting system by adding the term to the searcher(weighting.here())
    with indexer.searcher() as searcher:
        query = MultifieldParser(["name", "description"], schema=indexer.schema).parse(searchTerm)
        results = searcher.search(query)
        print("Length of results: " + str(len(results)))
        for line in results:
            print(line["name"] + ": " + line["description"])

def createNewIndex():
    # check that our index directory exists
    checkForIndexDirectory()
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
    indexer = create_in(index_directory_name, schema)

    # get all the data from our database to add to the index
    print("Getting data from database...")
    columns = "name, description, alias, application, capability, user, limitation"
    powers = readSqlData(db_file, "SELECT {} FROM powers".format(columns))

    # add the database data to the index
    print("Creating index...")
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
    print("Index created.")
    return indexer

# execute some sql and return true on an error
def executeSql(dbfile: str, sql: str, values = None) -> bool:
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
        if (values == None):
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
        if (conn != None):
            conn.close()
    # return the error value
    return result

# execute some sql and return the data
def readSqlData(dbfile: str, sql: str, values = None) -> object:
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
        if (values == None):
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
        if (conn != None):
            conn.close()
    # return the error value
    return data

if __name__ == '__main__':
    main()
