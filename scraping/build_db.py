import csv
import json
import os
import sqlite3
import sys
from io import StringIO

# folder names
data_folder_name = "powerData"
scrape_folder_name = "scraping"

# file names
power_data_file_name = "powers_data.json"
db_file_name = "powers.db"

# attributes to find
alias_search = ["also cal", "also known", "also named"]
application_search = "application"
capabilities_search = "capabilit"
known_users_search = ["know users", "known user", "users"]
limitations_search = "limit"
associations_search = "associations"


def main():
    # get our paths
    files = get_paths()

    data_folder = files[data_folder_name]
    power_data_file = files[power_data_file_name]
    db_file = files[db_file_name]

    # check that our data folder exists
    if (os.path.isdir(data_folder) is False):
        # try to create the directory
        try:
            os.mkdir(data_folder)
        except Exception as e:
            # if unable to create the directory, tell the user and exit
            print(f"Unable to make data directory.\n{e}")
            sys.exit(1)

    # load our json from file
    json_data = None
    with open(power_data_file, "r") as f:
        json_data = json.load(f)

    # create the database file
    createDatabase(db_file)

    # variables for progress report
    progress_check = 0
    progress_total = len(json_data)

    for item in json_data:
        # progress report
        if (progress_check % 10 == 0):
            progress = (progress_check / progress_total) * 100
            printProgress(progress)
        progress_check += 1

        # the attributes we want to save
        name = ""
        description = ""
        alias = []
        application = []
        capability = []
        user = []
        limitation = []
        association = []

        # read the json and build our database
        for attribute in json_data[item]:
            level = attribute["level"]
            content = attribute["content"]
            title = attribute["title"]
            # get the name and description
            if (level == 1):
                name = title
                for c in content:
                    if (c["type"] == "paragraph"):
                        description = c["text"]
            # get the other attributes
            elif (level == 2):
                lower_title = title.lower()
                # get the alias
                if (any(word in lower_title for word in alias_search)):
                    getContent(content, alias)
                # get the application
                elif (application_search in lower_title):
                    getContent(content, application)
                # get the capability
                elif (capabilities_search in lower_title):
                    getContent(content, capability)
                # get the known users
                elif (any(word in lower_title for word in known_users_search)):
                    getContent(content, user)
                # get the limitation
                elif (limitations_search in lower_title):
                    getContent(content, limitation)
                # get the associations
                elif (associations_search in lower_title):
                    getContent(content, association)
            # get the extended known users
            elif (level == 3):
                getContent(content, user)
        # check if the power is a category
        if (not alias and not application and not capability and not user and not limitation and not association):
            # don't add the category
            continue
        else:
            # insert the row into the database
            insertRow(db_file, name, description, alias, application, capability, user, limitation, association)
    # final update to progress
    printProgress(100)


# get our file names and folder paths
def get_paths() -> dict:
    # file paths will get stored in a dictionary
    fileDict = {}
    # get our working folder
    cwd = os.getcwd()
    # get the base folder of our working folder
    base = os.path.basename(os.path.normpath(cwd))
    # check if our base is our target folder
    if (base == scrape_folder_name):
        # since our base is our target folder, create the paths without the base added
        fileDict[power_data_file_name] = os.path.join(cwd, data_folder_name, power_data_file_name)
        fileDict[db_file_name] = os.path.join(cwd, data_folder_name, db_file_name)
        fileDict[data_folder_name] = os.path.join(cwd, data_folder_name)
    else:
        # since our base is NOT our target folder, create the paths WITH the base added
        fileDict[power_data_file_name] = os.path.join(cwd, scrape_folder_name, data_folder_name, power_data_file_name)
        fileDict[db_file_name] = os.path.join(cwd, scrape_folder_name, data_folder_name, db_file_name)
        fileDict[data_folder_name] = os.path.join(cwd, scrape_folder_name, data_folder_name)
    # return our file paths
    return fileDict


# output current progress
def printProgress(progress):
    print(f" Building Database: {progress:.2f}%", end="\r".rjust(5))


# add content to an existing list
def getContent(content, in_list):
    for c in content:
        # if the type is a list, then add each element to the list
        if (c["type"] == "list"):
            for e in c["elements"]:
                in_list.append(e["text"])
        # if the type is text, then just add it to the list
        elif (c["type"] == "paragraph"):
            in_list.append(c["text"])


def createDatabase(dbfile: str):
    # database schema:
    # primary key: name
    # powers ( name (text), description (text), alias (text), application (text),
    #          capability (text), user (text), limitation (text) )

    # the sql to create the table
    sql = """CREATE TABLE IF NOT EXISTS powers (
                name TEXT,
                description TEXT,
                alias TEXT,
                application TEXT,
                capability TEXT,
                user TEXT,
                limitation TEXT,
                association TEXT,
                PRIMARY KEY (name)
            )"""
    # execute the sql statement
    executeSql(dbfile, sql)


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


# insert or replace a row in our database
def insertRow(dbfile: str, name: str, description: str, alias: list, application: list,
              capability: list, user: list, limitation: list, association: list):
    # our database's column names
    columns = "name, description, alias, application, capability, user, limitation, association"
    # the sql statement we will execute
    sql = f"INSERT OR REPLACE INTO powers ({columns}) VALUES(?,?,?,?,?,?,?,?)"
    # our values we are going to inser
    values = (name, description, listToCsv(alias), listToCsv(application),
              listToCsv(capability), listToCsv(cleanUser(user)),
              listToCsv(limitation), listToCsv(cleanAssociation(association)))
    executeSql(dbfile, sql, values)


# remove any 'see also' type users
def cleanUser(user_list: list) -> list:
    # create a new list
    cleaned_list = []
    # go through each know user
    for user in user_list:
        # and remove any that are 'see also'
        if ("see also:" not in user.lower()):
            cleaned_list.append(user)
    # return our cleaned list
    return cleaned_list


# remove any extra text from associated powers
def cleanAssociation(associate_list: list) -> list:
    # create a new list
    cleaned_list = []
    # go through each association
    for associate in associate_list:
        # remopve any that have forward slashes
        if ("/" in associate):
            continue
        # split the line at each space
        split = associate.split(" ")
        # this is the string we are going to build
        new_string = ""
        # our stop boolean
        word_not_capitalized = False
        # loop through the split word
        for word in split:
            # check that we have a word
            if (len(word) >= 1):
                # check if the first letter is a capital
                if (word[0].isupper()):
                    # some associations might have extra stuff behind it
                    if (":" in word):
                        # remove the color, and don't get any more words
                        word = word.replace(":", "")
                        word_not_capitalized = True
                    # add to our string we are building
                    new_string = f"{new_string} {word}"
                else:
                    # set our loop to stop
                    word_not_capitalized = True
                # stop when we have no more capitalized words
                if (word_not_capitalized is True):
                    break
            else:
                # skip the short word
                continue
        # if our new string is long enough, add the string to our list
        if (len(new_string) >= 4):
            cleaned_list.append(new_string.strip())
    # return our built list
    return cleaned_list


# convert a list to a csv style string
def listToCsv(in_list: list) -> str:
    # quote any strings in the list
    new_list = []
    for obj in in_list:
        if (isinstance(obj, str) is True):
            new_list.append(str(obj))
        else:
            new_list.append(obj)
    # create a stream for the csv writer
    output = StringIO()
    # create the csv writer
    writer = csv.writer(output, delimiter=',', quotechar='"')
    # write our string to the stream
    writer.writerow(new_list)
    # return the list as a comma separated string
    return output.getvalue()


if (__name__ == "__main__"):
    main()
