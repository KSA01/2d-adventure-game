#Server2D.py

import Database.database as db
import Network.rest as nw
import threading

Initialized = False

def MainThread():
    global Initialized
    while True:
        if not Initialized:
            continue

t = threading.Thread(target=MainThread)
t.start()

db.Init()
nw.Init()
Initialized = True

nw.Run()

'''db._mycursor.execute("SELECT * FROM gamesave WHERE name='me'")
print("Showing Player")
print(db._mycursor.fetchone())'''