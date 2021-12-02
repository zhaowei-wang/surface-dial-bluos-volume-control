import asyncio
from evdev import InputDevice
import requests
import xmltodict

class BluOSDevice(object):
    def __init__(self, ip, port, max_volume_level=70, step=2):
        # 0 to 100.
        self._max_volume_level = max_volume_level
        self._url = 'http://' + ip + ':' + str(port) + '/'
        self._step = step
        
        r = requests.get(self._url + 'Status')
        r = xmltodict.parse(r.content)
        self._current_volume = int(r['status']['volume'])

    def increase_volume(self):
        self._change_volume(self._step)

    def decrease_volume(self):
        self._change_volume(-self._step)

    def _change_volume(self, delta_volume):
        new_volume = self._current_volume + delta_volume
        if new_volume > self._max_volume_level:
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
    return event.type == 2 and event.code == 7 and event.value == 1

def rotated_counter_clockwise(event):
    return event.type == 2 and event.code == 7 and event.value == -1

async def volume_control(surface_dial_device, blu_os_device):
    button_held = False
    async for event in surface_dial_device.async_read_loop():
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
    surface_dial_device = InputDevice('/dev/input/event0')
    blu_os_device = BluOSDevice(ip='192.168.1.16', port=11000)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(volume_control(surface_dial_device, blu_os_device))

if __name__ == '__main__':
    main()
