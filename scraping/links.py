import csv
import os
import sqlite3
import sys
from io import StringIO
from urllib.parse import unquote

from bs4 import BeautifulSoup
from requests import Session

# folder names
data_folder_name = "powerData"
scrape_folder_name = "scraping"

# file names
links_db_file_name = "links.db"
powers_db_file_name = "powers.db"


def main():
        # get our paths
    files = get_paths()

    data_folder = files[data_folder_name]
    links_db_file = files[links_db_file_name]
    powers_db_file = files[powers_db_file_name]

    # check that our data folder exists
    if (os.path.isdir(data_folder) is False):
        # try to create the directory
        try:
            os.mkdir(data_folder)
        except Exception as e:
            # if unable to create the directory, tell the user and exit
            print(f"Unable to make data directory.\n{e}")
            sys.exit(1)

    # create our links database
    print(f"Creating {links_db_file_name}...")
    createDatabase(links_db_file)

    # get our known users from the powers database
    print(f"Getting known users from {powers_db_file_name}...")
    sql = "SELECT DISTINCT user FROM powers"
    known_users = readSqlData(powers_db_file, sql)

    # create a set of known users
    print(f"Creating known users list...")
    user_set = set()
    for user_tuple in known_users:
        # convert the csv string to a list so we can loop through it
        clean_users = csvStringToList(user_tuple[0])
        # if the list contains known users
        if (len(clean_users) >= 1):
            # don't add empty strings or any 'see also' known users
            for user in clean_users:
                if (user == ""):
                    continue
                if ("see also:" not in user.lower()):
                    user_set.add(user)
    # loop through the list and get a link for each user
    print("Getting links for known users, this will take a while...")
    user_dict = getUserLinks(user_set)
    # add the user and the link to a new database
    print(f"Adding links to {links_db_file_name}...")
    result = writeLinksToDatabase(links_db_file, user_dict)
    if (result is True):
        print("Done.")
    else:
        print("Failed to insert all links into database!")


def createDatabase(dbfile: str):
    # database schema:
    # primary key: name
    # powers ( name (text), link (text) )

    # the sql to create the table
    sql = """CREATE TABLE IF NOT EXISTS links (
                name TEXT,
                link TEXT,
                PRIMARY KEY (name)
            )"""
    # execute the sql statement
    executeSql(dbfile, sql)


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
        fileDict[links_db_file_name] = os.path.join(cwd, data_folder_name, links_db_file_name)
        fileDict[powers_db_file_name] = os.path.join(cwd, data_folder_name, powers_db_file_name)
        fileDict[data_folder_name] = os.path.join(cwd, data_folder_name)
    else:
        # since our base is NOT our target folder, create the paths WITH the base added
        fileDict[links_db_file_name] = os.path.join(cwd, scrape_folder_name, data_folder_name, links_db_file_name)
        fileDict[powers_db_file_name] = os.path.join(cwd, scrape_folder_name, data_folder_name, powers_db_file_name)
        fileDict[data_folder_name] = os.path.join(cwd, scrape_folder_name, data_folder_name)
    # return our file paths
    return fileDict


# this will take a list of users and search google.com for more information
def getUserLinks(user_set: set) -> dict:
    # try to get links, but if an exception occurs, return the input list
    try:
        # get our total and set our start count
        total = len(user_set)
        count = 0
        # show our progress bar
        print_progress(0.0)
        # the list or urls we are building
        linked_users = {}
        # create a requests session to try and speed up the process
        with Session() as session:
            # change user agents so google gives us a better page to search
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"}
            # go through the input user list
            for user in user_set:
                # search google.com for the user
                web_data = session.get(f"https://www.google.com/search?q={user}", timeout=(5, 15), headers=headers)
                # create a bs4 object and parse the returned page
                soup = BeautifulSoup(web_data.text, features="html.parser")
                # get the divs from the results
                divs = soup.findAll("div", attrs={"class": "r"})
                # set our stop variable
                found_link_for_user = False
                # loop through the divs looking for links
                for div in divs:
                    # check our stop variable
                    if (found_link_for_user is True):
                        # we found our link so move to the next user
                        break
                    # get all the links from the page so we can look through them
                    links = div.findAll("a", href=True)
                    # go through the links
                    for link in links:
                        domains = ["fandom.com", "wikia.com", "wikipedia.org"]
                        # and look for our wanted domains
                        if (any(domain in link["href"] for domain in domains)):
                            # unquote the link so it launches a new page correctly
                            clean_link = unquote(link["href"])
                            # create the link for our user and add to our list
                            linked_users[user] = clean_link
                            # we only need one link so we can stop our loop here
                            found_link_for_user = True
                            break
                # check if we found a link
                if (found_link_for_user is False):
                    # no links were found, just add the user
                    linked_users[user] = ""
                # update the count
                count = count + 1
                # update the progress
                if (count % 10 == 0):
                    percent = (count / total) * 100
                    print_progress(percent)
                # DEBUG: DELETE ME!
                if (count >= 25):
                    break
        # return our complete list
        print_progress(100.0)
        print()
        return linked_users
    except Exception as e:
        # if any exception happens, just return the original list
        print(f"USER LINKS FAILED! ({e})")
        return user_set


# execute some sql and return true on an error
def writeLinksToDatabase(links_db_file: str, links_dict: dict) -> bool:
    # a place to store the connection object
    conn = None
    # did the command return an error
    result = True
    # try to execute some sql
    try:
        # connect to the database (and create the file)
        conn = sqlite3.connect(links_db_file)
        # create a cursor
        cur = conn.cursor()
        # add all our links to the database
        sql = "INSERT OR REPLACE INTO links (name,link) VALUES(?,?)"
        for item in links_dict.items():
            cur.execute(sql, item)
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


# execute some sql and return true on an error
def executeSql(db_file: str, sql: str, values=None) -> bool:
    # a place to store the connection object
    conn = None
    # did the command return an error
    result = True
    # try to execute some sql
    try:
        # connect to the database (and create the file)
        conn = sqlite3.connect(db_file)
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
def readSqlData(db_file: str, sql: str, values=None) -> object:
    # a place to store the connection object
    conn = None
    # value returned from the sql statement
    data = None
    # try to execute some sql
    try:
        # connect to the database (and create the file)
        conn = sqlite3.connect(db_file)
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


# create a text progress bar
def print_progress(percent: float):
    # the number of bars to write
    bars = 50
    pendr = "|"
    pendl = "|"
    pchar = "█"
    nchar = "░"
    # the percentage each bar represents
    chunk = int(100 / bars)
    # the number of filled bars
    barcount = int(percent / chunk)
    # put all the peices together
    pbar = pendl + (barcount * pchar) + ((bars - barcount) * nchar) + pendr
    # output the progress bar
    sys.stdout.write(f"\r{pbar} {percent:.2f}%  ")
    sys.stdout.flush()


if (__name__ == "__main__"):
    main()
