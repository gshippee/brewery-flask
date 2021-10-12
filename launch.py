#!/bin/env python
from app import create_app, socketio
import atexit
import sys
from app.main import config
from time import sleep
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = create_app(debug=True)
def OnExitApp(user):
    f = open("write_db.txt","w")
    f.write('dont_write')
    f.close()
    config.h.close()
    config.bb.close()
    print(user, " exit Flask application")

atexit.register(OnExitApp, user='brewery')
if __name__ == '__main__':
    if config.DEBUG:
        config.h = []
        config.bb = []
    else:
        sys.path.insert(1, '/home/pi/Desktop/cython-hidapi')
        import hid
        from pylibftdi import BitBangDevice
        print(hid.enumerate())
        config.h = hid.device()
        config.h.open(5824,1503)
        config.h.set_nonblocking(1)
    try:
        config.bb=BitBangDevice()
    except:
        sleep(.5)
        config.bb=BitBangDevice()
    f = open("write_db.txt","w")
    f.write('write')
    f.close()
    socketio.run(app, host="0.0.0.0", port=5000, use_reloader=False)