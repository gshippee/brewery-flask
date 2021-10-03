'''Implements higher level functions based on relay states and temperature'''
from . import config
from time import sleep, time
from threading import Thread, active_count
import random

def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp_debug(device_file):
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

def turn_off_relay(relay):
    relay.turn_off()

def turn_on_relay(relay):
    relay.turn_on()

def kill_program():
    for thread in config.temp_threads:
        print(thread.name)
        thread.join()

def turn_off_all_relays():
    print('Turning off all relays')
    if not config.DEBUG:
        config.h.write([0x00, 0xfc]) 
        try:
            config.bb.port = 0
        except:
            sleep(.5)
            config.bb.port = 0
    for relay in config.relays:
        relay.active = False

def print_debug():
    get_relay_states()
    print('Active threads:', active_count(),'\n,\
        Duration:', round(config.duration,1), time(), '\n,\
        Current task:', config.task, config.task_marker, '\n,\
        Ready for task:',  config.ready_for_task,'\n,\
        Task Complete:',  config.task_complete,'\n,\
        Relay States:',  config.relay_states,'\n,\
        Temps:',  config.temps,'\n,\
        Counter Running:', config.counter_running)

def reset():
    config.thread = None
    config.tasks = []
    config.task = ''
    config.task_marker = 0
    config.sub_task = 0
    config.task_complete = False
    config.ready_for_task = False
    config.counter_running = False
    config.task_running = False
    config.duration = 0 

def get_task_info():
    try:
        task_items = config.tasks[config.task_marker]
        config.task = task_items[0]
        config.params = task_items[1]
    except Exception as e:
        print(e)
        reset()

def get_relay_states():
    config.relay_states = [relay.is_active() for relay in config.relays]

def restore_state():
    for relay, relay_state in enumerate(config.relay_states):
        if relay_state:
            print('RELAY', relay, config.relay_states[relay])
            config.relays[relay].turn_on()

def wait(start, end):
    while config.duration>=start and config.duration < end:
        sleep(.1)
        config.message = 'Waiting '+str(round(config.duration,1))+ ' '+str(round(start,1))+' '+ str(round(end,1))
        config.sub_task_str = 'Wait'
        print('Waiting '+str(round(config.duration,1))+ ' '+str(round(start,1))+' '+ str(round(end,1)))
        if not config.counter_running:
            get_relay_states()
            return 'Interrupt'
    return True

def pump_1_1(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.message = 'Turning on pump 1_1'
        print('Turning on pump_1_1')
        config.relays[config.PUMP_1_1].turn_on()
        config.sub_task+=1

    if config.sub_task == 1:
        config.sub_task_str = 'Wait'
        if wait(config.duration, duration) == 'Interrupt':
            return
        config.sub_task+=1

    if config.sub_task == 2:
        config.message = 'Turning off pump 1_1'
        print('Turning off pump_1_1')
        config.relays[config.PUMP_1_1].turn_off()

    print('Task complete')
    config.task_complete = True
    return

def pump_1_2(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.message = 'Turning on pump 1_2'
        print('Turning on pump 1_2')
        config.relays[config.PUMP_1_2].turn_on()
        config.sub_task+=1

    
    if config.sub_task == 1:
        config.sub_task_str = 'Wait'
        if wait(config.duration, duration) == 'Interrupt':
            return
        config.sub_task+=1

    if config.sub_task == 2:
        config.message = 'Turning off pump 1_2'
        print('Turning off pump 1_2')
        config.relays[config.PUMP_1_2].turn_off()

    print('Task complete')
    config.task_complete = True
    return

def pump_2_2(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.relays[config.PUMP_2_2_SWITCH].turn_on()
        config.sub_task_str = 'Turning on pump_2_2 switch'
        if wait(config.duration, 5) == 'Interrupt':
            return
        config.relays[config.PUMP_2_2_SWITCH].turn_off()
        config.sub_task+=1
    if config.sub_task == 1:
        config.relays[config.PUMP_2].turn_on()
        config.sub_task_str = 'Wait'
        if wait(5, 5+duration) == 'Interrupt':
            return
    config.task_complete = True
    return

def pump_2_no_switch(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.relays[config.PUMP_2].turn_on()
        config.sub_task_str = 'Wait'
        if wait(5, 5+duration) == 'Interrupt':
            return
    config.task_complete = True
    return

def pump_2_3(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.relays[config.PUMP_2_3_SWITCH].turn_on()
        config.sub_task_str = 'Turning on pump_2_3 switch'
        if wait(config.duration, 5) == 'Interrupt':
            return
        config.relays[config.PUMP_2_2_SWITCH].turn_off()
        config.sub_task+=1
    if config.sub_task == 1:
        config.relays[config.PUMP_2].turn_on()
        config.sub_task_str = 'Wait'
        if wait(5, 5+duration) == 'Interrupt':
            return
    config.task_complete = True
    return

def pump_3_3(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.relays[config.PUMP_3_3_ENABLE].turn_on()
        config.sub_task_str = 'Turning on pump_3_3 switch'
        if wait(config.duration, 5) == 'Interrupt':
            return
        config.relays[config.PUMP_3_3_ENABLE].turn_off()
        config.sub_task+=1
    if config.sub_task == 1:
        config.relays[config.PUMP_3_3].turn_on()
        config.sub_task_str = 'Wait'
        if wait(5, 5+duration) == 'Interrupt':
            return
    config.task_complete = True
    return

def pump_3_3(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.relays[config.SOLENOID].turn_on()
        config.sub_task_str = 'Turning on solenoid'
        if wait(config.duration, 5) == 'Interrupt':
            return
        config.relays[config.SOLENOID].turn_off()
        config.sub_task+=1
    if config.sub_task == 1:
        config.relays[config.PUMP_3_4_ENABLE].turn_on()
        config.sub_task_str = 'Turning on pump_3_4 switch'
        if wait(5, 10) == 'Interrupt':
            return
        config.sub_task+=1
    if config.sub_task == 2:
        config.relays[config.PUMP_3_4].turn_on()
        config.sub_task_str = 'Wait'
        if wait(10, 10+duration) == 'Interrupt':
            return
        config.relays[config.PUMP_3_4].turn_off()
        config.relays[config.PUMP_3_4_ENABLE].turn_off()
        config.sub_task+=1
    if config.sub_task == 3:
        config.relays[config.PUMP_3_3_ENABLE].turn_on()
        config.sub_task_str = 'Turning on pump_3_3 switch'
        if wait(10+duration, 10+duration+5) == 'Interrupt':
            return
        config.relays[config.PUMP_3_3_ENABLE].turn_off()

    config.task_complete = True
    return


def skip_task(num_skips=1):
        config.task_marker = config.task_marker + num_skips

def run_task():
    if config.task == 'pump_1_1':
        config.thread = Thread(target = pump_1_1, args = (config.params,))
        config.thread.start()

    if config.task == 'pump_1_2':
        config.thread = Thread(target = pump_1_2, args = (config.params,))
        config.thread.start()

    if config.task == 'pump_2_2':
        config.thread = Thread(target = pump_2_2, args = (config.params,))
        config.thread.start()

    if config.task == 'pump_2_3':
        config.thread = Thread(target = pump_2_3, args = (config.params,))
        config.thread.start()

    if config.task == 'pump_3_3':
        config.thread = Thread(target = pump_3_3, args = (config.params,))
        config.thread.start()
        


