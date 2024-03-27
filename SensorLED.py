import time
import datetime
from smbus2 import SMBus, i2c_msg
from bmp280 import BMP280
import paho.mqtt.client as mqtt
import wiringpi
import spidev
from class_LCD import LCD, ActivateLCD,DeactivateLCD
import sys

# ========== MQTT SETUP =============
# MQTT settings
MQTT_HOST ="mqtt3.thingspeak.com"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL =60
MQTT_TOPIC = "channels/2484833/publish"
MQTT_CLIENT_ID ="FQkPGzofGCkOLAYWNi89Oi0"
MQTT_USER ="FQkPGzofGCkOLAYWNi89Oi0"
MQTT_PWD = "6DEoGgDNIci62NMCQ6ckfoUP"

# MQTT error handling
def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("Connected OK with result code "+str(rc))
    else:
        print("Bad connection with result code "+str(rc))

def on_disconnect(client, userdata, flags, rc=0):
    print("Disconnected result code "+str(rc))

def on_message(client,userdata,msg):
    print("Received a message on topic: " + msg.topic + "; message: " + msg.payload)


# Set up a MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, MQTT_CLIENT_ID)
client.username_pw_set(MQTT_USER, MQTT_PWD)

# Connect callback handlers to client
client.on_connect= on_connect
client.on_disconnect= on_disconnect
client.on_message= on_message
print("Attempting to connect to %s" % MQTT_HOST)
client.connect(MQTT_HOST, MQTT_PORT)
client.loop_start() #start the loop


# =========== Create an I2C bus object
bus = SMBus(0)

# ================== BMP208 SENSOR ===========
address = 0x77
bmp280 = BMP280(i2c_addr= address, i2c_dev=bus)
interval = 1 # Sample period in seconds

# ================== BH1750 SENSOR ===========
address_bh170 = 0x23
bus.write_byte(address_bh170, 0x10)
bytes_read = bytearray(2)

#============= Get value from the BH1750 
def get_value(bus, address):
    write = i2c_msg.write(address, [0x10])
    read = i2c_msg.read(address, 2)
    bus.i2c_rdwr(write, read)
    bytes_read = list(read)
    # Corrected formula to calculate lux
    return (bytes_read[0] << 8 | bytes_read[1]) / 1.2

# ============= NOKIA 5110 CONNECTIONS ===============

PINS = {
    'RST' : 10,
    'CS' : 13, # CE
    'DC' : 9, # D/C
    'DIN' : 11,
    'SCLK' : 14, # CLK
    'LED' : 6, # LIGHT
}

wiringpi.wiringPiSetup()
wiringpi.wiringPiSPISetupMode(1, 0, 400000, 0) # (channel, port, speed, mode)
wiringpi.pinMode(PINS['CS'] , 1) # set pin to mode 1 (output)
ActivateLCD(PINS['CS'])
lcd_1 = LCD(PINS)

#========== SETUP FOR DIMMING LIGHT BASED ON LUX
# We are using a single input to light up two LEDs

luxPins = 12
current_brightness = 100
wiringpi.softPwmCreate(luxPins, 0, 100)
wiringpi.softPwmWrite(luxPins, 100)

# Change brightness automatically based on the lux value
def calculate_brightness(lux):
    if lux is None:
        return 100  # Default to off (inverted logic) if there's a reading error
    elif lux < 50:
        return 0    # Full brightness (inverted logic)
    elif 100 <= lux <= 200:
        return 70   # Medium brightness (inverted logic)
    elif lux > 200:
        return 100  # LED off (inverted logic)
    else:
        return 100  # Ensure function returns an integer for unexpected lux values

# PWM
def controlLEDs(sig1, target_brightness, current_brightness, step=1, wait=0.01):
    if target_brightness < current_brightness:
        for brightness in range(current_brightness, target_brightness - 1, -step):
            wiringpi.softPwmWrite(sig1, brightness)
            time.sleep(wait)
    elif target_brightness > current_brightness:
        for brightness in range(current_brightness, target_brightness + 1, step):
            wiringpi.softPwmWrite(sig1, brightness)
            time.sleep(wait)
            
# ============ BUTTONS SETUP TO CHANGE THE LUX and TEMPERATURE VALUES
# These buttons would change the lux and temperature value when pressed

def setup(button):
    wiringpi.wiringPiSetup()  # Initialize wiringPi setup
    wiringpi.pinMode(button, wiringpi.INPUT)  # Set pin to input mode
    wiringpi.pullUpDnControl(button, wiringpi.PUD_UP)  # Enable pull-up resistor

# Buttons for changing lux
pushBtns = [16, 15]
for button in pushBtns:
    setup(button)

# ================ FUNCTIONS TO CHANGE THE VALUES FOR LUX AND TEMPERATURE
# Change lux values
def changeLux(l, btn):
    for index, button in enumerate(btn):
        if wiringpi.digitalRead(button) == wiringpi.LOW:
            if index == 0:
                l += 50
            elif index == 1:
                l -= 50
            print(f"Button {index + 1} Pressed! Adjusted Light Level: {l} lux")
            time.sleep(0.1)  # Simple debounce
    return l

# Change temperature values
def changeTemp(l, btn):
    for index, button in enumerate(btn):
        if wiringpi.digitalRead(button) == wiringpi.LOW:
            if index == 0:
                l += 1.5
            elif index == 1:
                l -= 1.5
            print(f"Button {index + 1} Pressed! Adjusted Temp Value: {l} lux")
            time.sleep(0.1)  # Simple debounce
    return l

# Global variables to track the last button press time and manual adjustment status
# We are using this to make sure that we have a delay and the value doesn't get overriden if we press too quickly
last_button_press_time = 0
manual_adjustment_active = False
manual_lux_adjustment_duration = 3  # Duration to use the manually adjusted lux value

# ============== GPIOs STEPPER MOTOR ==========

pins = [2, 7, 4, 5]  # Define GPIO pins connected to stepper motor coils

# Setup stepper motor
def setupStepperMotor(pins):
    wiringpi.wiringPiSetup()
    for pin in pins:
        wiringpi.pinMode(pin, 1)  # Set pin to output mode

# Step function
def step(pins, sequence, delay):
    for coil in sequence:
        for pin in range(4):  # Assuming a 4-pin stepper motor
            wiringpi.digitalWrite(pins[pin], coil[pin])
        time.sleep(delay)

# Main function to rotate the stepper motor
def rotate_stepper(pins, steps, delay):
    # Define the step sequence for full stepping
    sequence = [[1,0,0,0],
                [0,1,0,0],
                [0,0,1,0],
                [0,0,0,1]]

    for _ in range(steps):
        for coil_state in sequence:
            step(pins, [coil_state], delay)

    # Reset the pins to low
    for pin in pins:
        wiringpi.digitalWrite(pin, 0)

setupStepperMotor(pins)  # Setup GPIO pins
# ================== FINAL LOOP TO RENDER EVERYTHING ============
try:
    lcd_1.clear()
    lcd_1.set_backlight(1)
    
    while True:
        dt = datetime.datetime.now()
        
        # Measure temperature and pressure from BMP280
        temperature = bmp280.get_temperature()
        pressure = bmp280.get_pressure()
        lux = get_value(bus, address_bh170)
    
        # Adjust lux based on button press
        lux = changeLux(lux, pushBtns)  
        temperature = changeTemp(temperature, pushBtns)  
        
        # Print Values On Terminal
        print('=======SENSOR VALUES START========')
        print(f'light Intensity:{lux:.2f}')
        print(f'Temperature:{temperature:.2f}')
        print(f'Pressure: {pressure:.2f}')
        print(dt)
        print('=======SENSOR VALUES ENDS========')
        
        # Change Brightness based on Lux
        target_brightness = calculate_brightness(lux)
        controlLEDs(luxPins, target_brightness, current_brightness, step=5)  # Adjust step size as needed
        current_brightness = target_brightness
        
        if temperature > 24:
            rotate_stepper(pins, steps=256, delay=0.01)
        
        # LCD setup
        ActivateLCD(PINS['CS'])
        lcd_1.clear() # clear buffer
        lcd_1.go_to_xy(0, 10) # starting position

        lcd_1.put_string(f'Lux:{lux:.2f}') # print to buffer
        lcd_1.put_string(f'\n')
        lcd_1.put_string(f'Temp:{temperature:.2f}') 
        
        # print to buffer
        lcd_1.refresh() # update the LCD with the buffer
        DeactivateLCD(PINS['CS'])
        
        # === MQTT DATA SEND
        MQTT_DATA = "field1="+str(lux)+"&field2="+str(temperature)+"&field3="+str(pressure)+"&status=MQTTPUBLISH"
        try:
            client.publish(topic=MQTT_TOPIC, payload=MQTT_DATA, qos=0, retain=False, properties=None)
            time.sleep(interval)
        except OSError:
            client.reconnect()
        time.sleep(2)

except KeyboardInterrupt:
    # deactivaten the LCD after code ended
    lcd_1.clear()
    lcd_1.refresh()
    lcd_1.set_backlight(0)
    DeactivateLCD(PINS['CS'])
    print("\nProgram terminated")   
