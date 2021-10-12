from multiprocessing import Pool
from time import sleep
import os
import glob
from datetime import datetime
import sqlite3
import io
import numpy as np
import random

def adapt_array(arr):
    """
    http://stackoverflow.com/a/31312102/190597 (SoulNibbler)
    """
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)


# Converts np.array to TEXT when inserting
sqlite3.register_adapter(np.ndarray, adapt_array)

# Converts TEXT to np.array when selecting
sqlite3.register_converter("array", convert_array)

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def get_db():
    db = sqlite3.connect(
        DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    #g.db.row_factory = sqlite3.Row
    db.row_factory = make_dicts
    return db


def close_db(e=None):
    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        print(db.executescript(f.read().decode('utf8')))

def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp_debug(device_file):
    sleep(2)
    return str(random.random()*50+device_file)

def read_temp(device_file):
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        sleep(.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return str(temp_c) 


if __name__ == '__main__':
    DEBUG = True
    SECRET_KEY='dev',
    DATABASE=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    DATABASE=os.path.join(DATABASE, 'brewery.sqlite')
    print(DATABASE)
    DATE_FMT = "%Y-%m-%d %H:%M:%S"
    base_dir = '/sys/bus/w1/devices/'


    device_folders = glob.glob(base_dir+'28*')
    if DEBUG:
        device_files = [0,0,0,0,0]
    else:
        device_files = [s+'/w1_slave' for s in device_folders]


    pool = Pool(len(device_files))
    db = get_db()
    while True:
        try:
            f = open("write_db.txt","r")
            lines = f.readlines()
            f.close()
            if 'dont' in lines[0]:
                print('Sleeping')
                sleep(10)
            else:
                if DEBUG:
                    temps = pool.map_async(read_temp_debug,device_files).get(5)
                else:
                    temps = pool.map(read_temp, device_files)
                datetime_now = datetime.now().strftime(DATE_FMT)
                print(datetime_now, temps)
                db.execute('INSERT INTO brewery_temps (brew_run, temps, date_time) VALUES (?, ?, ?)', ('DEBUG', np.array(temps), datetime_now ))
                db.commit()
                temp_data = db.execute('SELECT * FROM brewery_temps WHERE ID = (SELECT MAX(ID) FROM brewery_temps)').fetchall()
                print('RESPONSE', temp_data)
                sleep(.1)
        except KeyboardInterrupt:
            close_db()
            pool.close()
            pool.join()