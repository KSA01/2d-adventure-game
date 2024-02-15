#database.py

import mysql.connector
from mysql.connector import errorcode
import json

import ssl
ssl._create_default_https_context = ssl._create_default_https_context

DATABASE = "adventuredatabase"
GAMESAVE = "gamesave"
GAME_NAME = "name"
GAME_DATA = "chardata"

def NewChar(name, charData):
    global _mydb
    global _mycursor
    sql = "INSERT INTO " + GAMESAVE + " (" + GAME_NAME + ", " + GAME_DATA + ") VALUES (%s, %s)"
    val = (name, charData)
    _mycursor.execute(sql, val)
    _mydb.commit()

def Init():
    global _mydb
    global _mycursor

    try:
        _mydb = mysql.connector.connect(
            host = "localhost",
            port = "3306",
            user = "admin",
            passwd = "adminpass"
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database server is not running")
        else:
            print(err)
        return
    
    _mycursor = _mydb.cursor()
    _mycursor.execute("SHOW DATABASES")

    for result in _mycursor:
        if DATABASE in result:
            break
    else:
        #database not found - create it
        _mycursor.execute("CREATE DATABASE " + DATABASE)
        _mycursor.execute("USE " + DATABASE)
        _mycursor.execute("CREATE TABLE " + GAMESAVE + " (id INT AUTO_INCREMENT PRIMARY KEY, " + \
                          GAME_NAME + " VARCHAR(255), " + GAME_DATA + " JSON)")
        #add player to db
        NewChar("me", json.dumps({"x":320, "y":240}))

    _mydb = mysql.connector.connect(
        host = "localhost",
        port = "3306",
        user = "admin",
        passwd = "adminpass",
        database = DATABASE
    )    
    _mycursor = _mydb.cursor(buffered=True)

def GetCharData(id, name="me"):
    global _mycursor

    if id == 0:
        name = "me"
    elif id == 1:
        name = "you"
    elif id == 2:
        name = "enemy0"
    elif id == 3:
        name = "enemy1"

    _mycursor.reset()
    _mycursor.execute(f"SELECT chardata FROM gamesave WHERE name='{name}'")
    result = _mycursor.fetchone()
    #_mycursor.nextset()
    return result[0]

def GetCharPos(id):
    result = GetCharData(id)
    dict = json.loads(result)
    return dict['x'], dict['y']

def SetCharPos(id, x, y, name="me"):
    global _mydb
    global _mycursor

    if not isinstance(x, int) or not isinstance(y, int):
        return False

    if id == 0:
        name = "me"
    elif id == 1:
        name = "you"
    elif id == 2:
        name = "enemy0"
    elif id == 3:
        name = "enemy1"
    
    j = {'x':x, 'y':y}
    sql = "UPDATE gamesave SET chardata=%s WHERE name=%s"
    val = (json.dumps(j), name)
    _mycursor.reset()
    _mycursor.execute(sql, val)
    #_mycursor.nextset()
    _mydb.commit()

    return True

def ClearSave():
    global _mydb
    global _mycursor

    _mycursor.execute("DELETE FROM gamesave")
    _mydb.commit()