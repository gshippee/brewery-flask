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
        config.relay_states = [relay.is_active() for relay in config.relays]
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
        print('Waiting '+str(round(config.duration,1))+ ' '+str(round(start,1))+' '+ str(round(end,1)))
        if not config.counter_running:
            get_relay_states()
            return 'Interrupt'
    return True

def set_temp_1(args):
    args = args.split('|')
    target_temp = float(args[0])
    end_time = float(args[1])
    while True:
        sleep(1)
        course_temp = float(config.temps[0])
        fine_temp = float(config.temps[1])
        print(target_temp, end_time, course_temp, fine_temp)
        print(course_temp < target_temp, config.heat_on_1==False)
        print(config.sub_task_str)
        if (course_temp < target_temp and config.heat_on_1 == False):
            print('If 1')
            config.heat_on_1 = True
            config.sub_task_str = 'Heater 1 on'
            config.relays[config.HEATER_1].turn_on()

        if (course_temp > target_temp and fine_temp<target_temp):
            print('If 2')
            config.heat_on_1 = False
            config.sub_task_str = 'Heater 1 off. Recirc 1 on.'
            if config.relays[config.HEATER_1].is_active():
                config.relays[config.HEATER_1].turn_off()
            if not config.relays[config.PUMP_1_1].is_active():
                config.relays[config.PUMP_1_1].turn_on()

        if (course_temp > target_temp and fine_temp > target_temp):
            print('If 3')
            config.sub_task_str = 'Recirc 1 off.'
            config.heat_on_1 = False
            config.relays[config.PUMP_1_1].turn_off()

        if (config.duration > end_time and course_temp > target_temp and fine_temp+.5 > target_temp):
            config.relays[config.PUMP_1_1].turn_off()
            config.relays[config.HEATER_1].turn_off()
            print('Task complete')
            config.task_complete = True
            return

        if not config.counter_running:
            get_relay_states()
            config.heat_on_1 == False
            return 'Interrupt'

def set_temp_2(args):
    args = args.split('|')
    target_temp = float(args[0])
    end_time = float(args[1])
    while True:
        course_temp = float(config.temps[2])
        fine_temp = float(config.temps[3])
        if (course_temp < target_temp and config.heat_on_2 == False):
            config.heat_on_2 = True
            config.sub_task_str = 'Heater 2 on'
            config.relays[config.HEATER_2].turn_on()

        if (course_temp > target_temp and fine_temp<target_temp):
            config.heat_on_2 = False
            config.sub_task_str = 'Heater 2 off. Recirc 3 on.'
            if config.relays[config.HEATER_2].is_active():
                config.relays[config.HEATER_2].turn_off()
            if not config.relays[config.PUMP_3_3].is_active():
                config.relays[config.PUMP_3_3].turn_on()

        if (course_temp > target_temp and fine_temp > target_temp):
            config.sub_task_str = 'Recirc 3 off.'
            config.heat_on_2 = False
            config.relays[config.PUMP_3_3].turn_off()

        if (config.duration > end_time and course_temp > target_temp and fine_temp+.5 > target_temp):
            config.relays[config.PUMP_3_3].turn_off()
            config.relays[config.HEATER_2].turn_off()
            print('Task complete')
            config.task_complete = True
            return

        if not config.counter_running:
            get_relay_states()
            config.heat_on_2 == False
            return 'Interrupt'

def set_temp_2_drop(args):
    args = args.split('|')
    target_temp = float(args[0])
    end_time = float(args[1])
    while True:
        course_temp = float(config.temps[2])
        fine_temp = float(config.temps[3])
        if (course_temp > target_temp and config.heat_on_1 == False):
            config.sub_task_str = 'Wait pump 3-3 to cool'
            config.relays[config.PUMP_3_3].turn_on()

        if (config.duration > end_time and course_temp < target_temp and fine_temp+.5 > target_temp):
            config.relays[config.PUMP_3_3].turn_off()
            print('Task complete')
            config.task_complete = True
            return

        if not config.counter_running:
            get_relay_states()
            config.heat_on_2 == False
            return 'Interrupt'

def set_temp_2_no_recirc(args):
    args = args.split('|')
    target_temp = float(args[0])
    end_time = float(args[1])
    while True:
        course_temp = float(config.temps[2])
        fine_temp = float(config.temps[3])
        if (course_temp < target_temp and config.heat_on_2 == False):
            config.sub_task_str = 'Heater 2 On'
            config.heat_on_2 = True
            config.relays[config.HEATER_2].turn_on()

        if course_temp > target_temp:
            config.heat_on_2 = False
            config.sub_task_str = 'Heater 2 off'
            if config.relays[config.HEATER_2].is_active():
                config.relays[config.HEATER_2].turn_off()

        if (config.duration > end_time and course_temp > target_temp):
            if config.relays[config.HEATER_2].is_active():
                config.relays[config.HEATER_2].turn_off()
            print('Task complete')
            config.task_complete = True
            return

        if not config.counter_running:
            get_relay_states()
            config.heat_on_2 == False
            return 'Interrupt'

def pump_1_1(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.message = 'Turning on pump 1_1'
        print('Turning on pump_1_1')
        config.relays[config.PUMP_1_1].turn_on()
        config.sub_task+=1

    if config.sub_task == 1:
        config.sub_task_str = 'Wait pump 1-1'
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
        config.sub_task_str = 'Wait pump 1-2'
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
        config.sub_task_str = 'Wait pump 2-2'
        if wait(5, 5+duration) == 'Interrupt':
            return
        config.relays[config.PUMP_2].turn_off()
    config.task_complete = True
    return

def pump_2_no_switch(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.relays[config.PUMP_2].turn_on()
        config.sub_task_str = 'Wait Pump 2'
        if wait(5, 5+duration) == 'Interrupt':
            return
        config.relays[config.PUMP_2].turn_off()
    config.task_complete = True
    return

def calc_efr(pfr, dfr, on_time, min_off_time):
    mefr = pfr*on_time/(on_time+min_off_time)
    if mefr>dfr:
        off_time = pfr*on_time/dfr-on_time
    else:
        off_time = min_off_time
    return off_time

def pump_fr_2_2(args):
    print(args)
    args = args.split('|')
    on_time = float(args[0])
    min_off_time = float(args[1])
    num_gals = float(args[2])
    dfr = float(args[3])
    pfr = .305 #5g/min
    off_time = calc_efr(pfr, dfr, on_time, min_off_time )
    num_iterations = num_gals/dfr/(off_time+on_time)*60
    print(on_time, off_time, min_off_time, num_gals, num_iterations)
    if config.sub_task == 0:
        config.relays[config.PUMP_2_2_SWITCH].turn_on()
        config.sub_task_str = 'Turning on pump_2_2 switch'
        if wait(config.duration, 5) == 'Interrupt':
            return
        config.relays[config.PUMP_2_2_SWITCH].turn_off()
        config.sub_task+=1
    for i in range(1, int(num_iterations)+1):
        if config.sub_task == i*2-1:
            config.relays[config.PUMP_2].turn_on()
            config.sub_task_str = 'Wait Pump 2 On, '+str(i)
            start = 5+(on_time+off_time)*(i-1)
            end = 5+(on_time+off_time)*(i-1)+on_time
            if wait(start, end) == 'Interrupt':
                return
            config.relays[config.PUMP_2].turn_off()
            config.sub_task+=1
        if config.sub_task == i*2:
            start = 5+(on_time+off_time)*(i-1)+on_time
            end = 5+(on_time+off_time)*(i-1)+on_time+off_time
            config.sub_task_str = 'Wait Pump 2 Off, '+str(i)
            if wait(start, end) == 'Interrupt':
                return
            config.sub_task+=1
    fraction = num_iterations-int(num_iterations)
    i+=1
    if config.sub_task == i*2-1:
        config.relays[config.PUMP_2].turn_on()
        config.sub_task_str = 'Wait Pump 2 On Fraction'
        start = (on_time+off_time)*(i-1)
        end = (on_time+off_time)*(i-1)+on_time*fraction
        if wait(start, end) == 'Interrupt':
            return
        config.relays[config.PUMP_2].turn_off()
        config.sub_task+=1
    if config.sub_task == i*2:
        start = (on_time+off_time)*(i-1)
        end = (on_time+off_time)*(i-1)+on_time*fraction+off_time*fraction
        config.sub_task_str = 'Wait Pump 2 Off Fraction'
        if wait(start, end) == 'Interrupt':
            return
        config.sub_task+=1
    config.task_complete = True
    return


def pump_2_3(duration):
    duration = float(duration)
    if config.sub_task == 0:
        config.relays[config.PUMP_2_3_SWITCH].turn_on()
        config.sub_task_str = 'Turning on pump_2_3 switch'
        if wait(config.duration, 5) == 'Interrupt':
            return
        config.relays[config.PUMP_2_3_SWITCH].turn_off()
        config.sub_task+=1
    if config.sub_task == 1:
        config.relays[config.PUMP_2].turn_on()
        config.sub_task_str = 'Wait Pump 2-3'
        if wait(5, 5+duration) == 'Interrupt':
            return
        config.relays[config.PUMP_2].turn_off()
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
        config.sub_task_str = 'Wait Pump 3-3'
        if wait(5, 5+duration) == 'Interrupt':
            return
        config.relays[config.PUMP_3_3].turn_off()
    config.task_complete = True
    return

def pump_3_4(duration):
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
        config.sub_task_str = 'Wait pump 3-4'
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

def relay_test(args):
    relay, duration = args.split('|')
    relay = int(relay)
    duration = float(duration)
    if config.sub_task == 0:
        config.relays[relay].turn_on()
        config.sub_task_str = 'Wait'
        if wait(config.duration,config.duration+duration) == 'Interrupt':
            return
        config.relays[relay].turn_off()
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

    if config.task == 'pump_2_no_switch':
        config.thread = Thread(target = pump_2_no_switch, args = (config.params,))
        config.thread.start()

    if config.task == 'pump_fr_2_2':
        config.thread = Thread(target = pump_fr_2_2, args = (config.params,))
        config.thread.start()

    if config.task == 'pump_fr_2_3':
        config.thread = Thread(target = pump_fr_2_3, args = (config.params,))
        config.thread.start()

    if config.task == 'pump_2_3':
        config.thread = Thread(target = pump_2_3, args = (config.params,))
        config.thread.start()

    if config.task == 'pump_3_3':
        config.thread = Thread(target = pump_3_3, args = (config.params,))
        config.thread.start()
        
    if config.task == 'pump_3_4':
        config.thread = Thread(target = pump_3_4, args = (config.params,))
        config.thread.start()

    if config.task == 'set_temp_1':
        config.thread = Thread(target = set_temp_1, args = (config.params,))
        config.thread.start()

    if config.task == 'set_temp_2':
        config.thread = Thread(target = set_temp_2, args = (config.params,))
        config.thread.start()

    if config.task == 'set_temp_2_drop':
        config.thread = Thread(target = set_temp_1, args = (config.params,))
        config.thread.start()

    if config.task == 'set_temp_2_no_recirc':
        config.thread = Thread(target = set_temp_1, args = (config.params,))
        config.thread.start()

    if config.task == 'relay_test':
        config.thread = Thread(target = relay_test, args = (config.params,))
        config.thread.start()