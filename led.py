from machine import Pin

class Led:
    _state: bool
    _pin: Pin

    def __init__(self):
        self._pin = Pin("LED", Pin.OUT)
        self._state = False
        self._pin.off()
    
    def toggle(self):
        self._pin.toggle()
    
    def off(self):
        self._pin.off()

    def on(self):
        self._pin.on()
