#!/bin/env python
from app import create_app, socketio
from app.main import config
from multiprocessing import Pool
app = create_app(debug=True)
if __name__ == '__main__':
    config.pool = Pool(len(config.device_files))
    try:
        socketio.run(app)
    except KeyboardInterrupt:
        pool.close()
        pool.join()