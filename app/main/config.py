'''File containing all the variables that represent the relay assignment of the various physical components'''
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

pool = None
DEBUG = True

HEATER_POT_1 = 1
PUMP_1_1 = 2
PUMP_1_2 = 3
PUMP_2_2_SWITCH = 4
PUMP_2_3_SWITCH = 5
PUMP_2 = 11
HEATER_POT_3 = 6 
PUMP_3_3_ENABLE = 14
PUMP_3_3 = 7
PUMP_3_4_ENABLE = 12
PUMP_3_4 = 13
SOLENOID = 8

NUM_RELAYS = 16

DATE_FMT = "%Y-%m-%d %H:%M:%S"
if DEBUG:
    h = []
    bb = []
else:
    sys.path.insert(1,'/home/pi/Desktop/cython-hidapi')
    import hid
    from pylibftdi import BitBangDevice
    #Relay stuff
    try:
        h = hid.device()
        h.open(5824,1503) # TREZOR VendorID/ProductID
        h.set_nonblocking(1)
        print("Opened device")
    except IOError as ex:
        print(ex)
        print("You probably don't have the hard coded device. Update the hid.device line")
        print("in this script with one from the enumeration list output above and try again.")

    try:
        bb = BitBangDevice()
    except:
        sleep(.5)
        bb = BitBangDevice()
start_loop = 0
end_loop = 0
tasks = []
thread = None
task = ''
task_marker = 0
sub_task = 0
sub_task_str = ''
task_complete = False
ready_for_task = False
counter_running = False
task_running = False
duration = 0 
message = ''
load_tasks = False

if not DEBUG:
    base_dir = '/sys/bus/w1/devices/'
    device_folders = glob.glob(base_dir+'28*')
    device_files = [s+'/w1_slave' for s in device_folders]
else:
    device_files = [0,1,2,3,4]
temps = [0 for thermometer in device_files]
temp_threads = []
collecting_temps = False

class Relay:
    def __init__(self, relay_num):
        self.active = False
        self.relay_num = relay_num
    def is_active(self):
        return self.active
    def turn_on(self):
        if self.relay_num <= 8:
            if not DEBUG:
                h.write([0x00,0xff,int(str(self.relay_num),16)])
            self.active = True
        else:
            try:
                if not DEBUG:
                    bb.port ^= relay_map[str(self.relay_num)]
                self.active = True
            except:
                sleep(.5)
                if not DEBUG:
                    bb.port ^= relay_map[str(self.relay_num)]
                self.active = True
                print("Error with relay")
        return self.relay_num

    def turn_off(self):
        if self.relay_num <= 8:
            if not DEBUG:
                h.write([0x00,0xfd,int(str(self.relay_num),16)])
            self.active = False
        else:
            try:
                if not DEBUG:
                    bb.port &= 255-relay_map[str(self.relay_num)]
                self.active = False
            except:
                sleep(.5)
                if not DEBUG:
                    bb.port &= 255-relay_map[str(self.relay_num)]
                self.active = False

        return self.relay_num

relays = []
for i in range(1,NUM_RELAYS):
    relays.append(Relay(i))

relay_states = [0 for relay in relays]
print(relay_states)