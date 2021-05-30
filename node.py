from sensorclass import Sensor
from machine import Pin
import time

# gmclock - grandmother clock control with stepper
# Started 2/13/2020

state = Sensor("state", "VS", initval=False, save=True)
status = Sensor("status", "VS", initval="unknown")

# Set some constants to make things easier to remember
Chime = True
Silent = False
Enable = False
Disable = True

# swing is number of steps between on and off
swing = Sensor("swing", "VS", initval=600)

qsense = Sensor("qsense", "IN", 4, offname="chime detected", onname="Silent")

stepperDir = Sensor("Direction", "OUT", 13, onname="Chime", offname="Silent", initval=Silent )
stepperStep = Sensor("Step", "OUT", 15)
stepperState = Sensor("Enable", "OUT", 12, onname="Disabled", offname="Enabled")
# Disable stepper coils
stepperState.setstate(Disable)
stepperDelay = Sensor("Delay", "VS", initval=700)

# Direction True = Chime, False = Silent
# move function handle auto back-off to relieve pressure on lever
def move(steps, direction, delay=stepperDelay.value):
    stepperDir.setstate(direction)
    stepperState.setstate(Enable)
    # Move stepper
    for i in range(0,steps):
        stepperStep.pin.value(0)
        time.sleep_us(delay)
        stepperStep.pin.value(1)
        time.sleep_us(delay)
    # Back off stepper 10 steps
    stepperDir.setstate(not direction)
    for i in range(0,20):
        stepperStep.pin.value(0)
        time.sleep_us(delay)
        stepperStep.pin.value(1)
        time.sleep_us(delay)
    # Disable stepper coils
    stepperState.setstate(Disable)


# Called from main.py
def main():
    from time import time
    lastsense = time() - 500
    allowchange = False
    print("allowchange false")
    Sensor.MQTTSetup("gmclock")
    while True:
        Sensor.Spin()
        if state.triggered and status.value == "unknown":
            status.setvalue("Chime") if state.state else status.setvalue("Silent")
            state.triggered = False
        if state.triggered:
            if state.state and status.value == "Silent":
                # Enable chime
                print("Chime on")
                move(swing.value, Chime)
                status.setvalue("Chime")
                state.triggered = False
            if not state.state and status.value == "Chime" and allowchange:
                # set silent
                print("Chime off")
                move(swing.value, Silent)
                status.setvalue("Silent")
                state.triggered = False
        if qsense.triggered:
            qsense.triggered = False
            allowchange = False
            lastsense = time()
        if not allowchange and (time() - lastsense) > 60 and (time() - lastsense) < 400:
            allowchange = True
            print("allowchange true")
        if allowchange and (time() - lastsense) > 400:
            allowchange = False
            print("allowchange false")
