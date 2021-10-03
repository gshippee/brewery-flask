from os import name
from threading import Thread, active_count
from flask import session, request
from flask_socketio import emit, join_room, leave_room
from .. import socketio
from time import sleep, time
from . import config, commands
from datetime import datetime
from .db import get_db
import numpy as np


@socketio.on('bootstrap_init', namespace='/brewery')
def bootstrap_init(message):
    db = get_db()
    temp_data = db.execute('SELECT * FROM brewery_temps WHERE brew_run = ?', ('DEBUG',)).fetchall()[-100:]
    try:
        time = list([i['date_time'] for i in temp_data])
        temps1 = list(np.array([i['temps'] for i in temp_data])[:,0].astype(float))
        temps2 = list(np.array([i['temps'] for i in temp_data])[:,1].astype(float))
        temps3 = list(np.array([i['temps'] for i in temp_data])[:,2].astype(float))
        temps4 = list(np.array([i['temps'] for i in temp_data])[:,3].astype(float))
        temps5 = list(np.array([i['temps'] for i in temp_data])[:,4].astype(float))
    except Exception as e:
        print(e, 'couldnt get temps')
        temps = []
    if len(temps1)==0:
        #emit('bootstrap', {'x': [datetime.now().strftime(config.DATE_FMT)], 'y': [0]})
        emit('bootstrap', {'time': [datetime.now().strftime(config.DATE_FMT)], 'temp1': [0], 'temp2':[0], 'temp3':[0], 'temp4':[0], 'temp5':[0]})
    else:
        print(temps1, temps2, temps3, temps4, temps5)
        emit('bootstrap', {'time': time, 'temp1': temps1, 'temp2': temps2, 'temp3':temps3, 'temp4':temps4, 'temp5': temps5})

@socketio.on('refreshed', namespace='/brewery')
def refreshed(message):
    config.load_tasks = True

counter = 0
@socketio.on('heartbeat_check', namespace='/brewery')
def hearbeat(message):
    sleep(.1)
    print(config.tasks)

    monitor_dict = {'threads': active_count(),\
        'duration': round(config.duration,1),\
        'current_task': config.task,\
        'subtask': config.sub_task_str,\
        'relay_states': config.relay_states,\
        'running': config.counter_running}
    emit('monitor', monitor_dict)

    print(config.load_tasks)
    if config.load_tasks:
        config.load_tasks = False
        task_str = ['|'.join(task) for task in config.tasks]
        emit('load_tasks', {'tasks':task_str, 'marker':config.task_marker})

    config.end_loop= time()
    if config.counter_running:
        config.duration +=config.end_loop-config.start_loop

    if config.task_complete:
        config.duration = 0
        config.task_complete = False
        config.task_marker += 1
        config.ready_for_task = True
        
    commands.get_task_info()

    if config.counter_running and config.ready_for_task:
        config.ready_for_task = False
        config.sub_task = 0
        print('NEXT TASK', config.sub_task, config.task, config.task_marker)
        config.load_tasks = True
        commands.run_task()

    global counter
    counter+=1
    if counter %10 == 0:
        commands.print_debug()

        if not config.DEBUG:
            config.temps = config.pool.map(commands.read_temp, config.device_files)
        else:
            config.temps = config.pool.map(commands.read_temp_debug, config.device_files)
        datetime_now = datetime.now().strftime(config.DATE_FMT)
        print(datetime_now, config.temps[0])

        db = get_db()
        db.execute('INSERT INTO brewery_temps (brew_run, temps, date_time) VALUES (?, ?, ?)', ('DEBUG', np.array(config.temps), datetime_now ))
        db.commit()	
#        emit('update', {'x': [datetime_now], 'y': [config.temps[0]]})
        emit('update', {'time': [datetime_now], 'temp1': [config.temps[0]], 'temp2': [config.temps[1]], 'temp3':[config.temps[2]], 'temp4':[config.temps[3]], 'temp5': [config.temps[4]]})
    config.start_loop = time()
    emit('heartbeat', {})

@socketio.on('stop', namespace='/brewery')
def stop(message):
    config.counter_running = False
    commands.get_relay_states()
    commands.turn_off_all_relays()

@socketio.on('go', namespace='/brewery')
def go(message):
    print('GO!', message)
    config.duration = 0
    config.sub_task = 0
    config.counter_running = False
    commands.turn_off_all_relays()
    commands.skip_task(num_skips=(message['marker']-config.task_marker)) 
    config.load_tasks = True

@socketio.on('add', namespace='/brewery')
def add(message):
    config.tasks.insert(config.task_marker+1,[message['action'], message['parameters']])
    config.load_tasks = True

@socketio.on('start', namespace='/brewery')
def start(message):
    config.counter_running = True
    config.ready_for_task = True
    commands.restore_state()
    config.load_tasks = True

@socketio.on('reverse', namespace='/brewery')
def reverse(message):
    config.duration = 0
    config.sub_task = 0
    config.counter_running = False
    commands.turn_off_all_relays()
    commands.skip_task(num_skips=-1) 
    config.load_tasks = True

@socketio.on('skip', namespace='/brewery')
def skip(message):
    config.duration = 0
    config.sub_task = 0
    config.counter_running = False
    commands.turn_off_all_relays()
    commands.skip_task(num_skips=1) 
    config.load_tasks = True

@socketio.on('reset', namespace='/brewery')
def reset(message):
    commands.reset()
    config.load_tasks = True

@socketio.on('quit', namespace='/brewery')
def quit(message):
    print('Killing program')
    commands.kill_program()