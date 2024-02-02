from machine import Pin, Timer

class Led:
    _state: bool
    _pin: Pin
    _timer: Timer	# ms
    _initT = False
    
    LED_SLOW_PERIOD_MS = 1000
    LED_FAST_PERIOD_MS = 200

    def __init__(self):
        self._pin = Pin("LED", Pin.OUT)
        self._state = False
        self._pin.off()
    
    def toggle(self):
        self._pin.toggle()
        
    def _Toggle_Cb(self, timer):
        self._pin.toggle()
    
    def off(self):
        self._pin.off()

    def on(self):
        self._pin.on()
        
    def blink(self, period_ms):
        if (False == self._initT):
            self._timer = Timer()
            self._timer.init(mode=Timer.PERIODIC, period=period_ms, callback=self._Toggle_Cb)
            self._initT = True
        else:
            self._timer.deinit()
            self._timer.init(mode=Timer.PERIODIC, period=period_ms, callback=self._Toggle_Cb)
            self._initT = True
