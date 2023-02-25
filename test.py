import serial
import time
import binascii
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class RPLidar_A1M8:
    """Interface to RPLidar A1M8 functionality"""
    def __init__(self, port='/dev/ttyUSB0'):
        self._port = port
        self._serial = serial.Serial(port=self._port, baudrate=115200, timeout=0.1)

    def stop(self):
        # Stop motor
        #self.motor(False)

        # Send stop request
        command = b'\xA5\x25'
        self._serial.write(command)
        time.sleep(0.001)
        self._serial.reset_input_buffer()

    def reset(self):
        # Send reset request
        command = b'\xA5\x40'
        self._serial.write(command)
        time.sleep(0.002)
        self._serial.reset_input_buffer()
        #s = self._serial.read(500)

    def motor(self, status: bool):
        self._serial.dtr = not status

    def scan(self):
        # Start motor
        self.motor(True)

        # Send scan request
        command = b'\xA5\x20'
        self._serial.write(command)
        s = self._serial.read(7)
        if s.hex() != 'a55a0500004081':
            raise RuntimeError("Could not start scan")

    def get_data(self):
        """Capture a new scan"""
        data = {'S':[], 'C':[], 'Quality':[], 'Angle':[], 'Distance':[]}
        capture = False

        self.scan()
        while True:
            # Read data response packets
            s = self._serial.read(5)
            if len(s) == 5:
                quality = s[0] >> 2
                Sb = bool((s[0] & 0b10) >> 1)
                S = bool(s[0] & 0b01)
                C = bool(s[1] & 0x01)
                angle = ((s[2] << 7) + (s[1] >> 1)) / 64.0 # In degrees
                distance = ((s[4] << 8) + s[3]) / 4000.0 # In meters

                isvalid = (Sb == (not S)) and C and (quality > 0)

                if (S == 1) and capture:
                    break

                if S == 1 and not(capture):
                    capture = True

                if capture and isvalid:
                    data['S'].append(S)
                    data['C'].append(C)
                    data['Quality'].append(quality)
                    data['Angle'].append(angle/180*math.pi)
                    data['Distance'].append(distance)

        self.stop()
        return data

    def get_info(self):
        # Send info request
        command = b'\xA5\x50'
        self._serial.write(command)
        s = self._serial.read(7)
        if s.hex() == 'a55a1400000004':
            s = self._serial.read(20)
            return {'Model':s[0], 'Major':s[2], 'Minor':s[1], 'Hardware':s[3]}
        else:
            print("Received {0}".format(s.hex()))
            raise RuntimeError("Could not read the info response")

    def get_health(self):
        # Send health request
        command = b'\xA5\x52'
        self._serial.write(command)
        s = self._serial.read(7)
        if s.hex() == 'a55a0300000006':
            s = self._serial.read(3)
            return s[0];
        else:
            print("Received {0}".format(s.hex()))
            raise RuntimeError("Could not read health response")
        return status[code]

    def get_sample_rate(self):
        # Send sample rate request
        command = b'\xA5\x59'
        self._serial.write(command)
        s = self._serial.read(7)
        if s.hex() == 'a55a0400000015':
            s = self._serial.read(4)
            Tss = (s[1] << 8) + s[0] # In us
            Tse = (s[3] << 8) + s[2] # In us
            return {'Standard':1.0e6/Tss, 'Express':1.0e6/Tse}
        else:
            raise RuntimeError("Could not read sample rate response")
        return



def show(lidar):
    fig = plt.figure()
    ax = fig.add_subplot(projection='polar')
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    def animate(i):
        data = lidar.get_data()
        ax.clear()
        ax.set_ylim(0,4)
        sc = ax.scatter(data['Angle'], data['Distance'], c='r', marker='o', s=1)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        return sc,

    ani = animation.FuncAnimation(fig, animate, interval=2000, blit=True, save_count=50)
    plt.show()



lidar = RPLidar_A1M8()

code = lidar.get_health()
status = {0:'Good', 1:'Warning', 2:'Error'}
print('Status: {0}'.format(status[code]))

data = lidar.get_info()
print("Model: {0}  Firmware: {1}.{2} Hardware: {3}".format(data['Model'], data['Major'], data['Minor'], data['Hardware']))

rate = lidar.get_sample_rate()
print('Sample rate (standard): {0} Hz   Sample rate (express): {1} Hz'.format(rate['Standard'], rate['Express']))


# Show data
show(lidar)
lidar.motor(False)
time.sleep(2)

