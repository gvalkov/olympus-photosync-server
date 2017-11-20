# Code adapted from: https://github.com/timwaizenegger/raspberrypi-examples/blob/master/actor-led-7segment-4numbers/tm1637.py

import time
import RPi.GPIO as GPIO


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


class TM1637:
    ADDR_AUTO = 0x40
    ADDR_FIXED = 0x44
    ADDR_START = 0xC0

    BRIGHTNESS_DARKEST = 0
    BRIGHTNESS_TYPICAL = 2
    BRIGHTNESS_HIGHEST = 7

    HEXDIGITS = [
        0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d,
        0x07, 0x7f, 0x6f, 0x77, 0x7c, 0x39, 0x5e, 0x79, 0x71
    ]

    def __init__(self, clk, dio, brightness=BRIGHTNESS_TYPICAL):
        self.clk = clk
        self.dio = dio
        self.brightness = brightness

        self.colon_on = False
        self.current_value = [0, 0, 0, 0]

        GPIO.setup(self.clk, GPIO.OUT)
        GPIO.setup(self.dio, GPIO.OUT)

    def clear(self):
        b = self.brightness
        point = self.colon_on
        self.brightness = 0
        self.colon_on = False
        data = [0x7F, 0x7F, 0x7F, 0x7F]
        self.show(data)
        self.brightness = b
        self.colon_on = point

    def show_num(self, i):
        if isinstance(i, int):
            s = '%04d' % min(9999, i)
        else:
            s = str(i)
        self.show(list(map(int, s)))

    def show(self, data):
        for i in range(4):
            self.current_value[i] = data[i]

        self.start()
        self.write_byte(self.ADDR_AUTO)
        self.stop()
        self.start()
        self.write_byte(self.ADDR_START)
        for i in range(4):
            self.write_byte(self.coding(data[i]))
        self.stop()
        self.start()
        self.write_byte(0x88 + self.brightness)
        self.stop()

    def set_brightness(self, value):
        if value > 7:
            value = 7
        elif value < 0:
            value = 0

        if self.brightness != value:
            self.values = value
            self.show(self.current_value)

    def show_colon(self):
        self.colon_on = True
        self.show(self.current_value)

    def hide_colon(self):
        self.colon_on = False
        self.show(self.current_value)

    def write_byte(self, data):
        for i in range(8):
            GPIO.output(self.clk, GPIO.LOW)
            if data & 0x01:
                GPIO.output(self.dio, GPIO.HIGH)
            else:
                GPIO.output(self.dio, GPIO.LOW)
            data = data >> 1
            GPIO.output(self.clk, GPIO.HIGH)

        GPIO.output(self.clk, GPIO.LOW)
        GPIO.output(self.dio, GPIO.HIGH)
        GPIO.output(self.clk, GPIO.HIGH)
        GPIO.setup(self.dio, GPIO.IN)

        while GPIO.input(self.dio):
            time.sleep(0.001)
            if GPIO.input(self.dio):
                GPIO.setup(self.dio, GPIO.OUT)
                GPIO.output(self.dio, GPIO.LOW)
                GPIO.setup(self.dio, GPIO.IN)
        GPIO.setup(self.dio, GPIO.OUT)

    def start(self):
        GPIO.output(self.clk, GPIO.HIGH)
        GPIO.output(self.dio, GPIO.HIGH)
        GPIO.output(self.dio, GPIO.LOW)
        GPIO.output(self.clk, GPIO.LOW)

    def stop(self):
        GPIO.output(self.clk, GPIO.LOW)
        GPIO.output(self.dio, GPIO.LOW)
        GPIO.output(self.clk, GPIO.HIGH)
        GPIO.output(self.dio, GPIO.HIGH)

    def coding(self, data):
        point_data = 0x80 if self.colon_on else 0
        data = 0 if data == 0x7F else self.HEXDIGITS[data] + point_data
        return data


if __name__ == '__main__':
    d = TM1637(23, 24)
    d.clear()

    for i in range(0, 9999):
        i = [int(i) for i in '%04d' % i]
        d.show(i)
