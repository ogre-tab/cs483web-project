import csv
import os
import sqlite3
import sys
from io import StringIO

from whoosh.analysis import LanguageAnalyzer
from whoosh.fields import TEXT, Schema
from whoosh.index import Index, create_in, exists_in, open_dir
from whoosh.qparser import MultifieldParser, OrGroup, FuzzyTermPlugin
from whoosh.query import Phrase


# simple class to store data about a power
class PowerData:
    def __init__(self, name, description, alias, application, capability, user, limitation, association):
        self.name = name
        self.description = description
        self.alias = self.csvStringToList(alias)
        self.application = self.csvStringToList(application)
        self.capability = self.csvStringToList(capability)
        self.user = self.csvStringToList(user)
        self.limitation = self.csvStringToList(limitation)
        self.association = self.csvStringToList(association)
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
        if (self.association is None):
            self.association = []
        if (self.path is None):
            self.path = ""

    # convert a string with a csv format into a list
    def csvStringToList(self, in_str: str) -> list:
        # check if the string is none
        if (in_str is None):
            return []
        # check if the string is empty
        if (in_str == ""):
            return []
        # create an in memory file
        str_io = StringIO(in_str)
        # load the file into the csv reader
        csv_r = csv.reader(str_io, delimiter=',', quotechar='"')
        # get a list from the reader
        csv_list = list(csv_r)
        # for some reason the list is wrapped in a list
        if (len(csv_list) > 0):
            # check if our list is empty, and return the first element
            return csv_list[0]
        else:
            # otherwise, return an empty list
            return []

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"{self.name}: {self.description}"


# handles creation of the whoosh index and methods to get data from the index and database
class PowerIndex:
    def __init__(self):
        # folder names
        self._data_folder_name = "powerData"
        self._index_folder_name = "indexing"
        self._scrape_folder_name = "scraping"
        self._whoosh_index_folder_name = "whooshIndex"
        # file names
        self._powers_db_file_name = "powers.db"
        self._links_db_file_name = "links.db"
        # paths
        self.whoosh_index_folder = None
        self.powers_db_file = None
        self.links_db_file = None
        # whoosh index
        self.index = None
        # the schema our index will use
        self.schema = None
        # initialize the object
        self.initialize()

    # get the data our object needs
    def initialize(self):
        # get our file and folder paths
        self._get_paths()
        # create our analyzer
        analyzer = LanguageAnalyzer("en")
        # create the schema for our index
        self.schema = Schema(name=TEXT(stored=True, analyzer=analyzer),
                             description=TEXT(stored=True, analyzer=analyzer),
                             alias=TEXT(stored=True),
                             application=TEXT(stored=True, analyzer=analyzer),
                             capability=TEXT(stored=True, analyzer=analyzer),
                             user=TEXT(stored=True),
                             limitation=TEXT(stored=True, analyzer=analyzer))
        # load or create or index
        self.index = self.checkAndLoadIndex()

    # get our file names and folder paths
    def _get_paths(self):
        # get our working folder
        cwd = os.getcwd()
        # get the base folder of our working folder
        base = os.path.basename(os.path.normpath(cwd))
        # check if our base is our target folder
        if (base == self._index_folder_name):
            # since our base is our target folder, create the paths without the base added
            self.whoosh_index_folder = os.path.join(cwd, self._whoosh_index_folder_name)
        else:
            # since our base is NOT our target folder, create the paths WITH the base added
            self.whoosh_index_folder = os.path.join(cwd, self._index_folder_name, self._whoosh_index_folder_name)
        # add our database path that should not be in the base folder
        self.powers_db_file = os.path.join(cwd, self._scrape_folder_name, self._data_folder_name, self._powers_db_file_name)
        self.links_db_file = os.path.join(cwd, self._scrape_folder_name, self._data_folder_name, self._links_db_file_name)

    # look for an existing working index or create a new index
    def checkAndLoadIndex(self) -> Index:
        # check if our index directory exists
        if (os.path.isdir(self.whoosh_index_folder) is False):
            try:
                # create the index directory
                os.mkdir(self.whoosh_index_folder)
            except Exception as e:
                # print an error and exit
                print(f"Unable to create index directory '{self.whoosh_index_folder}':\n{e}")
                sys.exit(1)
            # our index directory doesn't exist, so create our index and return it
            return self.createNewIndex()
        else:
            # check if our index is valid
            if (exists_in(self.whoosh_index_folder) is False):
                # our index is invalid, so create our index and return it
                return self.createNewIndex()
            # try to load the index
            indexer = self._loadIndexFromDisk()
            # check if the index was loaded
            if (indexer is None):
                # build and return the index because the index didn't load
                return self.createNewIndex()
            elif (indexer.is_empty is True):
                # build and return the index because the index is empty
                return self.createNewIndex()
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
                    return self.createNewIndex()
                # get the number of rows in our database
                try:
                    db_count = self.readSqlData("SELECT COUNT(name) FROM powers")[0][0]
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
                    return self.createNewIndex()

    def search(self, searchTerm):
        # list of tuples containing our search results
        search_results = []
        # NOTE: can add a different weighting system by adding the term to the searcher(weighting.here())
        with self.index.searcher() as searcher:
            # our attributes to search in
            columns = ["name", "description", "alias", "application", "capability", "user", "limitation"]
            # create our query
            parser = MultifieldParser(columns, schema=self.index.schema, group=OrGroup)
            parser.add_plugin(FuzzyTermPlugin())
            query = parser.parse(searchTerm)
            # search our index with our query
            max_results = None
            results = searcher.search(query, limit=max_results)
            # get exact title matches
            exact_phrase = Phrase("name", searchTerm.split(" "))
            results_exact = searcher.search(exact_phrase, limit=None)
            # upgrade the exact match with all other results
            results_exact.upgrade_and_extend(results)
            # display the results
            for line in results_exact:
                # add the name to our search results
                search_results.append(line["name"])
        # return the data we got from the search results
        return search_results

    # don't call this method directly, call checkAndLoadIndex() instead
    def _loadIndexFromDisk(self):
        # try to load our index from disk
        try:
            # load the index from our specified directory
            indexer = open_dir(self.whoosh_index_folder, schema=self.schema)
            # return the loaded index
            print("Loaded index.")
            return indexer
        except Exception:
            # something happened while loading our index, return None
            return None

    def createNewIndex(self):
        # create the index our specified directory
        print("Building index.")
        indexer = create_in(self.whoosh_index_folder, self.schema)

        # get all the data from our database to add to the index
        print("Getting data from database...")
        columns = "name, description, alias, application, capability, user, limitation"
        powers = self.readSqlData(f"SELECT {columns} FROM powers")

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
                                limitation=power[6])
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
    def executeSql(self, sql: str, values=None) -> bool:
        # a place to store the connection object
        conn = None
        # did the command return an error
        result = True
        # try to execute some sql
        try:
            # connect to the database (and create the file)
            conn = sqlite3.connect(self.powers_db_file)
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
    def readSqlData(self, sql: str, values=None) -> object:
        # a place to store the connection object
        conn = None
        # value returned from the sql statement
        data = None
        # try to execute some sql
        try:
            # connect to the database (and create the file)
            conn = sqlite3.connect(self.powers_db_file)
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
    def getPower(self, powername: str) -> PowerData:
        columns = "name, description, alias, application, capability, user, limitation, association"
        power = self.readSqlData(f"SELECT {columns} FROM powers WHERE name=?", values=[powername])
        # should only have one result from the SQL, set our power entries to the first item
        if power is None or (len(power) < 1):
            return None

        if (len(power) >= 1):
            power = power[0]

        # create the power data object and return it
        power_data = PowerData(*power)
        return power_data

    # Try for a case-insensitive exact match
    def getTitleMatch(self, powername):
        titles = self.readSqlData(f"SELECT name FROM powers WHERE name like \"{powername}\"")
        if titles is not None and len(titles) > 0:
            # Step 1: steal Trenton's CSV stringy code thingy
            # Step 2: Profit
            str_io = StringIO(titles[0][0])
            csv_r = csv.reader(str_io)
            csv_list = list(csv_r)
            if (len(csv_list) > 0):
                print(csv_list)
                return csv_list[0]
        return None


def main():
    # create or load our index
    whooshIndex = PowerIndex()

    # test our index
    print(whooshIndex.search("flight"))


if __name__ == '__main__':
    main()
