#!/usr/bin/python3

import asyncio
from evdev import InputDevice
import requests
import time
import xmltodict

def epoch_ms():
    return round(time.time() * 1000)

class BluOSDevice(object):
    def __init__(self, ip, port, max_volume_level=60, step=2, dead_time_ms=50):
        # 0 to 100.
        self._max_volume_level = max_volume_level
        self._url = 'http://' + ip + ':' + str(port) + '/'
        self._step = step
        self._dead_time_ms = dead_time_ms
        
        r = requests.get(self._url + 'Status')
        r = xmltodict.parse(r.content)
        self._current_volume = int(r['status']['volume'])
        self._time_since_last_action = epoch_ms()

    def increase_volume(self):
        self._change_volume(self._step)

    def decrease_volume(self):
        self._change_volume(-self._step)

    def _change_volume(self, delta_volume):
        current_time = epoch_ms()
        if current_time - self._time_since_last_action < self._dead_time_ms:
            return
        else:
            self._time_since_last_action = current_time
        
        new_volume = self._current_volume + delta_volume
        if delta_volume > 0 and new_volume > self._max_volume_level:
            print('Exceeded max volume', self._max_volume_level)
            return
        
        url = self._url + 'Volume?level=' + str(new_volume)
        r = requests.get(url)
        r = xmltodict.parse(r.content)
        self._current_volume = int(r['volume']['#text'])

        print('Volume level', self._current_volume)

def button_pressed(event):
    return event.type == 1 and event.code == 256 and event.value == 1

def button_released(event):
    return event.type == 1 and event.code == 256 and event.value == 0

def rotated_clockwise(event):
    return event.type == 2 and event.code == 7 and event.value > 0

def rotated_counter_clockwise(event):
    return event.type == 2 and event.code == 7 and event.value < 0

async def volume_control(surface_dial_device, blu_os_device):
    button_held = False
    async for event in surface_dial_device.async_read_loop():
        print(repr(event))
        if button_pressed(event):
            print('Button pressed.')
            button_held = True
        elif button_released(event):
            print('Button released.')
            button_held = False
        elif rotated_clockwise(event):
            print('Rotated CW.')
            if button_held:
                  blu_os_device.increase_volume()
        elif rotated_counter_clockwise(event):
            print('Rotated CCW.')
            if button_held:
                  blu_os_device.decrease_volume()
            
        

def main():
    while True:
        try:
            surface_dial_device = InputDevice('/dev/input/event0')
            break
        except:
            print('/dev/input/event0 not available...')
            time.sleep(3)
    blu_os_device = BluOSDevice(ip='192.168.1.7', port=11000)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(volume_control(surface_dial_device, blu_os_device))

if __name__ == '__main__':
    main()
