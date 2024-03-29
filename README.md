
# Table of Contents
[**PROJECT OVERVIEW**	2](#_toc162477358)

[Goals and Objectives:	2](#_toc162477359)

[**Hardware and Software used**	2](#_toc162477360)

[Hardware:	2](#_toc162477361)

[Software, Libraries, and Protocols:	2](#_toc162477362)

[**System architecture & Setup**	3](#_toc162477363)

[1. Measuring Light Intensity (Lux):	3](#_toc162477364)

[2. Measuring Temperature and Pressure:	5](#_toc162477365)

[3. Controlling PWM LED intensity:	7](#_toc162477366)

[4. Changing the Lux value based on input from push down buttons:	9](#_toc162477367)

[5. Controlling the stepper motor based on temperature:	12](#_toc162477368)

[a.BMP280 connection:	12](#_toc162477369)

[b.Adding ULN2003:	13](#_toc162477370)

[c.Adding Stepper Motor:	14](#_toc162477371)

[6. Adding Nokia 5110 LCD:	16](#_toc162477372)

[7. Using MQTT for ThingSpeak:	18](#_toc162477373)

[**APPENDICES**	20](#_toc162477374)

[Project Code: https://github.com/nsyed78/indi-project	20](#_toc162477375)

[Youtube Video:	20](#_toc162477376)

[**SELF EVALUATION**	21](#_toc162477377)





# <a name="_hlk162386315"></a><a name="_toc162477358"></a>**PROJECT OVERVIEW**
## <a name="_toc162477359"></a>Goals and Objectives:
Use sensors to determine the temperature, light intensity, and pressure and based on that imitates a process. Send the values to an online dashboard for visualization and analysis.

For instance, if the temperature is above 25°C the stepper motor rotates imitating a fan, similarly if the lux value is below 50 the LED lights on the bread board light up.

# <a name="_toc162477360"></a>**Hardware and Software used**
## <a name="_toc162477361"></a>Hardware:
- OrangePi 3 LTS
- BH1750
- BMP280
- Stepper Motor
- ULN2003 Stepper Motor Controller
- PWM LED
- Nokia 5110 LCD
- 220-ohm Resistors
## <a name="_toc162477362"></a>Software, Libraries, and Protocols:
**Software:** We are using ThingSpeak as an online dashboard to visualize the data. By utilizing the MQTT we can push the data to ThingSpeak Channels.

**Libraries:** The language used to program the orangePi is python and we are using a few python libraries and protocols to communicate between the sensors and the device.

We are using the following libraries from python:

- SMBus for i2c for connecting our sensors
- BMP280 Library
- Paho for MQTT communications
- WiringPi for GPIO 
- Spidev for Nokia LCD

These are all the libraries that we are using for this whole project;
```
import time

import datetime

from smbus2 import SMBus, i2c\_msg

from bmp280 import BMP280

import paho.mqtt.client as mqtt

import wiringpi

import spidev

from class_LCD import LCD, ActivateLCD,DeactivateLCD

import sys
```
# <a name="_toc162477363"></a>**System architecture & Setup**
## <a name="_toc162477364"></a>1. Measuring Light Intensity (Lux):
We are using **BH1750 sensor** for measuring the lux value. The connection utilizes a breadboard.

|OPI Pins|GPIO|Sensor|
| :- | :- | :- |
|1|3\.3V |VCC|
|6|GND|GND|
|3|SCK|SCL|
|4|SDA|SDA|

![](https://github.com/nsyed78/indi-project/blob/e0fd7812db3b28970bc8d8ce9f8de86bfa10c307/Schematics/1.jpg)

**CODE:**

To initialize the sensor
```
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

 while True:
      # Measure temperature and pressure from BMP280
      lux = get_value(bus, address_bh170)
	 print(lux)

```

## <a name="_toc162477365"></a>2. Measuring Temperature and Pressure:
We are using **BMP280 sensor** for measuring the temperature and pressure. We are using Jumpers to connect the sensor with the same pins used for BH1750 sensor.

|OPI Pins|GPIO|Sensor|
| :- | :- | :- |
|1|3\.3V |VIN|
|6|GND|GND|
|3|SCK|SCK|
|4|SDA|SDI|

![](https://github.com/nsyed78/indi-project/blob/e0fd7812db3b28970bc8d8ce9f8de86bfa10c307/Schematics/2.jpg)

**CODE:**
```
# Create an I2C bus object
bus = SMBus(0)
address = 0x76

# Setup BMP280
bmp280 = BMP280(i2c_addr= address, i2c_dev=bus)
interval = 1 # Sample period in seconds

while True:
    # Measure data
    bmp280_temperature = bmp280.get_temperature()
    bmp280_pressure = bmp280.get_pressure()
    print("Temperatur

```
## <a name="_toc162477366"></a>3. Controlling PWM LED intensity:
By integrating the PWM LED with the BH1750 we are creating an imitation where we adjust the intensity of PWM LED based on how much lux value the sensor reads.

The code adjusts the intensity as follows:

- If the lux value is below 50 the LED lights up to 100%
- If the lux value is between 100 – 200 the LED lights up by only 30%
- If the lux is above 200 the LED goes to 0%

We are using inverted logic as we are using voltage and the GPIO inputs only on the LED and that is changing the way it lights up.

|OPI Pins|GPIO|LED|
| :- | :- | :- |
|1|3\.3V |Positive side with a 220 Ohm Resistor|
|21|w12|Using 2 LEDs from the same GPIO|

![A circuit board with wires](https://github.com/nsyed78/indi-project/blob/e0fd7812db3b28970bc8d8ce9f8de86bfa10c307/Schematics/3.jpg)

```
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
```

We are using the following code in the while loop to change the brightness of the LED

```
# Change Brightness based on Lux
        target_brightness = calculate_brightness(lux)
        controlLEDs(luxPins, target_brightness, current_brightness, step=5)  # Adjust step size as needed
        current_brightness = target_brightness

```
## <a name="_toc162477367"></a>4. Changing the Lux value based on input from push down buttons:
We are using two push down buttons to change the initial lux value that the sensor reads by 50. We are only using ground wire and GPIO inputs on the buttons for this. One side is connected to the ground wire and the other is connected to GPIO inputs for controlling the function of the buttons.

|OPI Pins|GPIO|LED|
| :- | :- | :- |
|24|W15 |Positive side with a 220 Ohm Resistor|
|26|W16|Using 2 LEDs from the same GPIO|
|6|GND|Using jumpers to use the same GND we are using for the sensors|

![](https://github.com/nsyed78/indi-project/blob/e0fd7812db3b28970bc8d8ce9f8de86bfa10c307/Schematics/4.jpg)
##
**CODE:** 
The following code is used to setup and change the values for the temperature and the pressure once pressed. 
```
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
```

In the final loop we reassign the values for the lux and the temperature via these functions and the code is as follows
```	
        # Adjust lux based on button press
        lux = changeLux(lux, pushBtns)  
        temperature = changeTemp(temperature, pushBtns)   
```
## <a name="_toc162477368"></a>5. Controlling the stepper motor based on temperature:
By using the BMP280, ULN2003 Stepper Motor Controller and Stepper Motor we are trying to imitate a fan that would spin based on the temperature reading from the sensor.

The function is as follows. 

If the temperature is above 25•C the motor starts spinning, or else the motor stops spinning.
### <a name="_toc162477369"></a>a.BMP280 connection:

|OPI Pins|GPIO|Sensor|
| :- | :- | :- |
|1|3\.3V |VIN|
|6|GND|GND|
|3|SCK|SCK|

![](https://github.com/nsyed78/indi-project/blob/e0fd7812db3b28970bc8d8ce9f8de86bfa10c307/Schematics/5.jpg)
### <a name="_toc162477370"></a>b.Adding ULN2003:*

----------------------------------------------

|OPI Pins|GPIO|ULN2003|
| :- | :- | :- |
|2 |5V|On the positive side of the board|
|9|GND|On the negative side of the board|
|7|w2|IN1|
|13|w7|IN2|
|10|w4|IN3|
|11|w5|IN4|

![](https://github.com/nsyed78/indi-project/blob/e0fd7812db3b28970bc8d8ce9f8de86bfa10c307/Schematics/6.jpg)

### <a name="_toc162477371"></a>c.Adding Stepper Motor:
By using the ULN2003 we are connecting the stepper motor.

![](https://github.com/nsyed78/indi-project/blob/e0fd7812db3b28970bc8d8ce9f8de86bfa10c307/Schematics/7.jpg)

**CODE:**

We are using the following code to run the stepper motor. We initialize the pins and define the step function. The rotate\_stepper functions define the sequence to rotate the motor
```
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

```

In the final loop we define the temperature threshold and simply run the rotate\_stepper function.

```
	if temperature > 24:
            rotate_stepper(pins, steps=256, delay=0.01)
```

## <a name="_toc162477372"></a>6. Adding Nokia 5110 LCD:
As a last step to enhance the project we are using a Nokia 5110 LCD to display the values on the screen for better readability.

By using Spidev we are able to communicate with the LCD via our orangepi.

The connections to the LCD are as follows:

|OPI Pins#|GPIO|LCD Pin#|
| :- | :- | :- |
|18|w10|RST|
|22|w13|CE|
|16|w9|D/C|
|19|MOSI/w11|DIN|
|23|SCLK|CLK|
|1|VCC 3.3V|VCC|
|12|w6|LIGHT|
|6|GND|GND|

![](https://github.com/nsyed78/indi-project/blob/e0fd7812db3b28970bc8d8ce9f8de86bfa10c307/Schematics/8.jpg)

**CODE:** 

We define the GPIO pins and initialize the LCD. 
```
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
```
In the final loop we have the following code to print on the screen
```
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

```
## <a name="_toc162477373"></a>7. Using MQTT for ThingSpeak:
By using the MQTT we are able to send the data from the sensors to an online dashboard that is ThingSpeak.

![ThingSpeak Dashboard](https://github.com/nsyed78/indi-project/blob/e0fd7812db3b28970bc8d8ce9f8de86bfa10c307/Schematics/9.jpg)

The code is as follows:
```
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
```
In the final loop we are pushing the payload to the ThingSpeak
```
        # === MQTT DATA SEND
        MQTT_DATA = "field1="+str(lux)+"&field2="+str(temperature)+"&field3="+str(pressure)+"&status=MQTTPUBLISH"
        try:
            client.publish(topic=MQTT_TOPIC, payload=MQTT_DATA, qos=0, retain=False, properties=None)
            time.sleep(interval)
        except OSError:
            client.reconnect()
```
# <a name="_toc162477374"></a>**APPENDICES**
### <a name="_toc162477376"></a>Youtube Video:  https://youtu.be/uc8oMEXdKZ0


