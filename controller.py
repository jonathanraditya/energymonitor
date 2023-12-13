import time 
import datetime
import requests
import RPi.GPIO as GPIO
import signal
from contextlib import contextmanager

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

GPIO.setmode(GPIO.BOARD)

RELAY_CONTROL = 40
THRESHOLDS = 0.33

def send_telegram_messages(messages):
    TOKEN = '2002016705:AAGcXBOdx_OAj5LSVxu1LAjVO_xIih8bdfA'
    CHAT_ID = '1293826547'
    # Send Messages
    send_message = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={messages}&parse_mode=markdown'
    res = requests.get(send_message)

def pump_state():
    MONITOR_PATH = "http://192.168.18.36/pumpstate"

    success = False
    attempt = 0
    call_help_attempt = 1
    while not success:
        try:
            with time_limit(10):
                res = requests.get(MONITOR_PATH)
            
            # If attempt success and
            # not becoming an error, proceed to next step
            success = True
        except (requests.exceptions.RequestException, OSError, TimeoutException):
            print(f'{datetime.datetime.now()} Attempt {attempt}, pump not responding.')
            attempt+=1
            
            # Sleep between attempt
            time.sleep(5)
            
        if (not success) & (attempt%10 == 0):
            # Every 10 failed attempts, send notification
            # to trigger additional action
            notif_success = False
            notif_attempt = 0
            while not notif_success:
                try:
                    messages = '*NEED ACTION*\nPump not responding!'
                    print(f'{datetime.datetime.now()} Attempt {call_help_attempt}, Call for help [{notif_attempt}].')
                    send_telegram_messages(messages)
                    notif_success = True
                    call_help_attempt+=1
                except (requests.exceptions.RequestException, TypeError):
                    notif_attempt+=1
                    time.sleep(5)
    
    return res.text

def pump_readings():
    pump_state_array = []
    for i in range(3):
        # Get state every 1 seconds
        get_pump_state = float(pump_state())
        pump_state_array.append(get_pump_state)
        time.sleep(1)

    readings = max(pump_state_array)
    return readings


# Default state
# GPIO.setup(RELAY_CONTROL, GPIO.OUT)

# BREAK_TIME = 270 # seconds
pump_on_records = './pump_on_records.txt'

while(True):
    readings = float(pump_state())

    if readings > THRESHOLDS:
        # GPIO.setup(RELAY_CONTROL, GPIO.IN)
        print(f'{datetime.datetime.now()} Value : {readings}. Pump turned on. Turn off AC until pump turned off.')
        pump_start_time = datetime.datetime.now()

        break_time_readings = float(pump_state())
        while break_time_readings > THRESHOLDS:
            # Continue to write pump electrical value readings to file
            # during BREAK_TIME
            break_time_readings = float(pump_state())

            # Update current_time
            current_time = datetime.datetime.now()

            with open(f'./record_details/{pump_start_time.timestamp()}.txt', 'a') as f:
                f.write(f'{current_time},{break_time_readings}\n')

        print(f'{datetime.datetime.now()} Value : {readings}. Pump turned off. Pump on time: {(current_time - pump_start_time).seconds}.')

        # Write pump_start_time and on time to file
        with open(pump_on_records, 'a') as f:
            f.write(f'{pump_start_time.timestamp()},{readings},{(current_time - pump_start_time).seconds}\n')

    else:
        # print(f'{datetime.datetime.now()} : Value : {readings}')
        # Normal state
        GPIO.setup(RELAY_CONTROL, GPIO.OUT)
