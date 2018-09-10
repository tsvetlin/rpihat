import time
import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import Adafruit_SSD1306
import Adafruit_DHT

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

SDI   = 17
RCLK  = 18
SRCLK = 27
RST = 24
PIN_BUTTON_14 = 14
PIN_BUTTON_15 = 15
PIN_BUTTON_4 = 4
PIN_DHT11=22

# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
tempSensor = Adafruit_DHT.DHT11

dispLeft = None
dispRight = None
buttonState14 = False
buttonState15 = False
buttonState4 = False
font = ImageFont.load_default()

def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SDI, GPIO.OUT)
    GPIO.setup(RCLK, GPIO.OUT)
    GPIO.setup(SRCLK, GPIO.OUT)
    GPIO.output(SDI, GPIO.LOW)
    GPIO.output(RCLK, GPIO.LOW)
    GPIO.output(SRCLK, GPIO.LOW)
    GPIO.setup(PIN_BUTTON_14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIN_BUTTON_15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIN_BUTTON_4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(PIN_BUTTON_15, GPIO.RISING, callback=button_callback)
    GPIO.add_event_detect(PIN_BUTTON_14, GPIO.RISING, callback=button_callback)
    GPIO.add_event_detect(PIN_BUTTON_4, GPIO.RISING, callback=button_callback)
    hc595_in(0)
    global dispLeft
    dispLeft = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3D)
    dispLeft.begin()
    dispLeft.clear()
    dispLeft.display()
    global dispRight
    dispRight = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)
    dispRight.begin()
    dispRight.clear()
    dispRight.display()

def hc595_in(dat):
        #print dat
	for bit in range(0, 20):
            val = 524288 & (dat << bit)
            #print val
            GPIO.output(SDI, val)
            GPIO.output(SRCLK, GPIO.HIGH)
            time.sleep(0.001)
            GPIO.output(SRCLK, GPIO.LOW)
	hc595_out()

def hc595_out():
	GPIO.output(RCLK, GPIO.HIGH)
	time.sleep(0.001)
	GPIO.output(RCLK, GPIO.LOW)
	
def button_callback(channel):
    print(channel)
    if channel == 15:
        global buttonState15
        buttonState15 = not buttonState15
        if buttonState15:
            measurePPM()
        else:
            dispLeft.clear()
            dispLeft.display()
    elif channel == 14:
        global buttonState14
        buttonState14 = not buttonState14
        if buttonState14:
            activateBar()
        else:
            hc595_in(0)
    elif channel == 4:
        global buttonState4
        buttonState4 = not buttonState4
        if buttonState4:
            measureTemp()
        else:
            dispRight.clear()
            dispRight.display()
    time.sleep(1)
    
def activateBar():
    values = [0]*2
    for i in range(2):
        values[i] = min(int(round(mcp.read_adc(i) / 100)),10)
        output = int(values [0] * '1' + (10 - values[0]) * '0' + values [1] * '1' + (10 - values[1]) * '0', 2)
        hc595_in(output) 

def displayLeft(leftPPM, rightPPM):
    width = dispLeft.width
    height = dispLeft.height
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.text((2, 2),    leftPPM,  font=font, fill=255)
    draw.text((2, 2+20), rightPPM, font=font, fill=255)
    dispLeft.image(image)
    dispLeft.display()
    
def measureTemp():
    humidity, temperature = Adafruit_DHT.read_retry(tempSensor, PIN_DHT11)
    if humidity is not None and temperature is not None:
        displayRight('Temp={0:0.1f}*C'.format(temperature), 'Humidity={0:0.1f}%'.format(humidity))
    else:
        measureTemp()
    
def measurePPM():
    values = [0]*2
    for i in range(2):
        values[i] = mcp.read_adc(i)
    if values[0] is not None and values[1] is not None:
            displayLeft('PPM_1={0:0.1f} PPM'.format(values[0]), 'PPM_2={0:0.1f} PPM'.format(values[1]))
    else:
        measurePPM()

def displayRight(temp, humidity):
    width = dispRight.width
    height = dispRight.height
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.text((2, 2),    temp,  font=font, fill=255)
    draw.text((2, 2+20), humidity, font=font, fill=255)
    dispRight.image(image)
    dispRight.display()
    
def measureSoil():
    print("Soil " +str(mcp.read_adc(2)))

print('Program is running, press Ctrl-C to quit...')

# Main program loop.
def loop():
    while True:
        measureSoil()
        time.sleep(1)
    
def destroy():
    GPIO.cleanup()

if __name__ == '__main__': # Program starting from here 
	setup() 
	try:
            loop()
	except KeyboardInterrupt:  
            destroy() 


