# Authors: Matteo Braiato 2024,
#
# This module borrows from the Adafruit BME280 Python library. Original
# Copyright notices are reproduced below.
#
# Those libraries were written for the Raspberry Pi. This modification is
# intended for the MicroPython and esp8266 boards.
#
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Based on the BMP280 driver with BME280 changes provided by
# David J Taylor, Edinburgh (www.satsignal.eu)
#
# Based on Adafruit_I2C.py created by Kevin Townsend.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import time
import machine
from ustruct import unpack, unpack_from
from array import array

# BME280 default address.
BME280_I2CADDR = 0x76

# Humidity oversampling (0xF2)
BME280_OSAMPLE_H_1  = 1
BME280_OSAMPLE_H_2  = 2
BME280_OSAMPLE_H_4  = 3
BME280_OSAMPLE_H_8  = 4
BME280_OSAMPLE_H_16 = 5

# Pressure oversampling (byte[7:5] 0xF4)
BME280_OSAMPLE_P_1  = 1
BME280_OSAMPLE_P_2  = 2
BME280_OSAMPLE_P_4  = 3
BME280_OSAMPLE_P_8  = 4
BME280_OSAMPLE_P_16 = 5

# Temperature oversampling (byte[4:2] 0xF4)
BME280_OSAMPLE_T_1  = 1
BME280_OSAMPLE_T_2  = 2
BME280_OSAMPLE_T_4  = 3
BME280_OSAMPLE_T_8  = 4
BME280_OSAMPLE_T_16 = 5

# Operating Mode (byte[1:0] 0xF4)
BME280_MODE_SLEEP   = 0 # sleep mode
BME280_MODE_FORCED  = 1 # forced mode (to be written for every read operation)
BME280_MODE_NORMAL  = 3 # normal mode (periodic readings)


BME280_REGISTER_CONTROL_HUM = 0xF2
BME280_REGISTER_STATUS      = 0xF3
BME280_REGISTER_CONTROL     = 0xF4


BME280_STATUSREG_MEASURE_MASK = 0x08 # bit 3 --> 1 if conv running, 0 if data saved on reg

controlRegCfg = 0

class BME280:

    def __init__(self,
                 mode=BME280_MODE_FORCED,
                 hos=BME280_OSAMPLE_H_1,
                 pos=BME280_OSAMPLE_P_1,
                 tos=BME280_OSAMPLE_T_1,
                 address=BME280_I2CADDR,
                 i2c=None,
                 **kwargs):
        # Check that mode is valid.
        if mode not in [BME280_MODE_SLEEP, BME280_MODE_FORCED, BME280_MODE_NORMAL]:
            raise ValueError(
                'Unexpected mode value {0}. Set mode to one of '
                'BME280_MODE_SLEEP (0x00), BME280_MODE_FORCED (0x01 or 0x02), or BME280_MODE_NORMAL (0x03)'.format(mode))
        self._mode = mode
        
        # Check that humidity oversample cfg is valid
        if hos not in [BME280_OSAMPLE_H_1, BME280_OSAMPLE_H_2, BME280_OSAMPLE_H_4,
                        BME280_OSAMPLE_H_8, BME280_OSAMPLE_H_16]:
            raise ValueError(
                'Unexpected mode value {0}. Set mode to one of '
                'BME280_OSAMPLE_H_1, BME280_OSAMPLE_H_2, BME280_OSAMPLE_H_4, BME280_OSAMPLE_H_8, or '
                'BME280_OSAMPLE_H_16'.format(mode))
        self._hos = hos
        
        # Check that pressure oversample cfg is valid
        if hos not in [BME280_OSAMPLE_P_1, BME280_OSAMPLE_P_2, BME280_OSAMPLE_P_4,
                        BME280_OSAMPLE_P_8, BME280_OSAMPLE_P_16]:
            raise ValueError(
                'Unexpected mode value {0}. Set mode to one of '
                'BME280_OSAMPLE_P_1, BME280_OSAMPLE_P_2, BME280_OSAMPLE_P_4, BME280_OSAMPLE_P_8, or '
                'BME280_OSAMPLE_P_16'.format(mode))
        self._pos = pos
        
        # Check that temperature oversample cfg is valid
        if hos not in [BME280_OSAMPLE_T_1, BME280_OSAMPLE_T_2, BME280_OSAMPLE_T_4,
                        BME280_OSAMPLE_T_8, BME280_OSAMPLE_T_16]:
            raise ValueError(
                'Unexpected mode value {0}. Set mode to one of '
                'BME280_OSAMPLE_T_1, BME280_OSAMPLE_T_2, BME280_OSAMPLE_T_4, BME280_OSAMPLE_T_8, or '
                'BME280_OSAMPLE_T_16'.format(mode))
        self._tos = tos
        
        # Check i2c
        self.address = address
        if i2c is None:
            raise ValueError('An I2C object is required.')
        self.i2c = i2c

        # load calibration data
        dig_88_a1 = self.i2c.readfrom_mem(self.address, 0x88, 26)
        dig_e1_e7 = self.i2c.readfrom_mem(self.address, 0xE1, 7)
        self.dig_T1, self.dig_T2, self.dig_T3, self.dig_P1, \
            self.dig_P2, self.dig_P3, self.dig_P4, self.dig_P5, \
            self.dig_P6, self.dig_P7, self.dig_P8, self.dig_P9, \
            _, self.dig_H1 = unpack("<HhhHhhhhhhhhBB", dig_88_a1)

        self.dig_H2, self.dig_H3 = unpack("<hB", dig_e1_e7)
        e4_sign = unpack_from("<b", dig_e1_e7, 3)[0]
        self.dig_H4 = (e4_sign << 4) | (dig_e1_e7[4] & 0xF)

        e6_sign = unpack_from("<b", dig_e1_e7, 5)[0]
        self.dig_H5 = (e6_sign << 4) | (dig_e1_e7[4] >> 4)

        self.dig_H6 = unpack_from("<b", dig_e1_e7, 6)[0]

        
        # load configuration
        controlHumidityCfg = self._hos
        self.i2c.writeto_mem(self.address, BME280_REGISTER_CONTROL_HUM,
                             controlHumidityCfg.to_bytes(1, 'big'))
        
        global controlRegCfg
        controlRegCfg = self._mode + (self._pos << 2) + (self._tos << 5)  
        self.i2c.writeto_mem(self.address, BME280_REGISTER_CONTROL,
                             controlRegCfg.to_bytes(1, 'big'))
        self.t_fine = 0

        # temporary data holders which stay allocated
        self._l1_barray = bytearray(1)
        self._l8_barray = bytearray(8)
        self._l3_resultarray = array("i", [0, 0, 0])

    def read_raw_data(self, result):
        """ Reads the raw (uncompensated) data from the sensor.

            Args:
                result: array of length 3 or alike where the result will be
                stored, in temperature, pressure, humidity order
            Returns:
                None
        """
        raw_temp = 0
        raw_hum = 0
        raw_press = 0
        # DEBUG
        #print("Mode = " + str(self._mode[0])) 
        if(self._mode == BME280_MODE_NORMAL):
            # check status if the read op is done and save data
            
            # check status
            self.i2c.readfrom_mem_into(self.address, BME280_REGISTER_STATUS, self._l1_barray)
            status = self._l1_barray[0]
            
            while(1 == (status & BME280_STATUSREG_MEASURE_MASK)):
                # conversion is running, wait
                time.sleep_us(1000)
            # conversion done, read data from register
            # burst readout from 0xF7 to 0xFE, faster than reading single values
            self.i2c.readfrom_mem_into(self.address, 0xF7, self._l8_barray)
            readout = self._l8_barray
            # pressure(0xF7): ((msb << 16) | (lsb << 8) | xlsb) >> 4
            raw_press = ((readout[0] << 16) | (readout[1] << 8) | readout[2]) >> 4
            # temperature(0xFA): ((msb << 16) | (lsb << 8) | xlsb) >> 4
            raw_temp = ((readout[3] << 16) | (readout[4] << 8) | readout[5]) >> 4
            # humidity(0xFD): (msb << 8) | lsb
            raw_hum = (readout[6] << 8) | readout[7]
                
        elif(self._mode == BME280_MODE_FORCED):
            # write forced mode, check status, save data
            
            # write forced mode
            self.i2c.writeto_mem(self.address, BME280_REGISTER_CONTROL,
                             controlRegCfg.to_bytes(1, 'big'))
            # check status if the read op is done and save data
            self.i2c.readfrom_mem_into(self.address, BME280_REGISTER_STATUS, self._l1_barray)
            status = self._l1_barray[0]
            
            while(1 == (status & BME280_STATUSREG_MEASURE_MASK)):
                # conversion is running, wait
                time.sleep_us(1000)
            # conversion done, read data from register
            # burst readout from 0xF7 to 0xFE, faster than reading single values
            self.i2c.readfrom_mem_into(self.address, 0xF7, self._l8_barray)
            readout = self._l8_barray
            # pressure(0xF7): ((msb << 16) | (lsb << 8) | xlsb) >> 4
            raw_press = ((readout[0] << 16) | (readout[1] << 8) | readout[2]) >> 4
            # temperature(0xFA): ((msb << 16) | (lsb << 8) | xlsb) >> 4
            raw_temp = ((readout[3] << 16) | (readout[4] << 8) | readout[5]) >> 4
            # humidity(0xFD): (msb << 8) | lsb
            raw_hum = (readout[6] << 8) | readout[7]
        else:
            # sleep mode, do nothing
            pass
        
        #self._l1_barray[0] = self._mode
        #self.i2c.writeto_mem(self.address, BME280_REGISTER_CONTROL_HUM,
        #                     self._l1_barray)
        #self._l1_barray[0] = self._mode << 5 | self._mode << 2 | 1
        #self.i2c.writeto_mem(self.address, BME280_REGISTER_CONTROL,
        #                     self._l1_barray)

        #sleep_time = 1250 + 2300 * (1 << self._mode)
        #sleep_time = sleep_time + 2300 * (1 << self._mode) + 575
        #sleep_time = sleep_time + 2300 * (1 << self._mode) + 575
        #time.sleep_us(sleep_time)  # Wait the required time

        result[0] = raw_temp
        result[1] = raw_press
        result[2] = raw_hum

    def read_compensated_data(self, result=None):
        """ Reads the data from the sensor and returns the compensated data.

            Args:
                result: array of length 3 or alike where the result will be
                stored, in temperature, pressure, humidity order. You may use
                this to read out the sensor without allocating heap memory

            Returns:
                array with temperature, pressure, humidity. Will be the one from
                the result parameter if not None
        """
        self.read_raw_data(self._l3_resultarray)
        raw_temp, raw_press, raw_hum = self._l3_resultarray
        
        # temperature
        var1 = ((raw_temp >> 3) - (self.dig_T1 << 1)) * (self.dig_T2 >> 11)
        var2 = (((((raw_temp >> 4) - self.dig_T1) *
                  ((raw_temp >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        temp = (self.t_fine * 5 + 128) >> 8

        # pressure
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = (((var1 * var1 * self.dig_P3) >> 8) +
                ((var1 * self.dig_P2) << 12))
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            pressure = 0
        else:
            p = 1048576 - raw_press
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.dig_P8 * p) >> 19
            pressure = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)

        # humidity
        h = self.t_fine - 76800
        h = (((((raw_hum << 14) - (self.dig_H4 << 20) -
                (self.dig_H5 * h)) + 16384)
              >> 15) * (((((((h * self.dig_H6) >> 10) *
                            (((h * self.dig_H3) >> 11) + 32768)) >> 10) +
                          2097152) * self.dig_H2 + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
        h = 0 if h < 0 else h
        h = 419430400 if h > 419430400 else h
        humidity = h >> 12

        if result:
            result[0] = temp
            result[1] = pressure
            result[2] = humidity
            return result

        return array("i", (temp, pressure, humidity))

    @property
    def values(self):
        """ human readable values """

        t, p, h = self.read_compensated_data()
        
        p = p // 256
        pi = p // 100
        pd = p - pi * 100

        hi = h // 1024
        hd = h * 100 // 1024 - hi * 100
        return ("{}C".format(t / 100), "{}.{:02d}hPa".format(pi, pd),
                "{}.{:02d}%".format(hi, hd))
