import sqlite3
import json

# file names
power_data_file = "powers_data.json"
db_file = "powers.db"

# attributes to find
alias_search = [ "also cal", "also known", "also named"]
application_search = "application"
capabilities_search = "capabilit"
known_users_search = [ "know users", "known user", "users" ]
limitations_search = "limit"

def main():
    # load our json from file
    json_data = None
    with open(power_data_file, "r") as f:
        json_data = json.load(f)

    # create the database file
    createDatabase(db_file)

    for item in json_data:
        # the attributes we want to save
        name = ""
        description = ""
        alias = []
        application = []
        capability = []
        user = []
        limitation = []

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
        # check if the power is a category
        if (not alias and not application and not capability and not user and not limitation):
            # don't add the category
            continue
        else:
            # insert the row into the database
            insertRow(db_file, name, description, alias, application, capability, user, limitation)

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
                PRIMARY KEY (name)
            )"""
    # execute the sql statement
    executeSql(dbfile, sql)

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

# insert or replace a row in our database
def insertRow(dbfile: str, name: str, description: str, alias: list, application: list,
                           capability: list, user: list, limitation: list):
    # our database's column names
    columns = "name, description, alias, application, capability, user, limitation"
    # the sql statement we will execute
    sql = "INSERT OR REPLACE INTO powers ({}) VALUES(?,?,?,?,?,?,?)".format(columns)
    # our values we are going to inser
    values = (name, description, listToCsv(alias), listToCsv(application),
              listToCsv(capability), listToCsv(user), listToCsv(limitation))
    executeSql(dbfile, sql, values)

# convert a list to a csv style string
def listToCsv(in_list: list) -> str:
    s = ""
    for item in in_list:
        if (s == ""):
            s = '"{}"'.format(item)
        else:
            s = '{},"{}"'.format(s, item)
    return s

if (__name__ == "__main__"):
    main()
