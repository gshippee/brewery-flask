#!/bin/env python
from app import create_app, socketio
import atexit
app = create_app(debug=True)
def OnExitApp(user):
    f = open("write_db.txt","w")
    f.write('dont_write')
    f.close()
    print(user, " exit Flask application")

atexit.register(OnExitApp, user='brewery')
if __name__ == '__main__':
    f = open("write_db.txt","w")
    f.write('write')
    f.close()
    socketio.run(app, host="0.0.0.0")