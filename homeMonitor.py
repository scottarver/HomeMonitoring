#!/usr/bin/env python
import Adafruit_BBIO.GPIO as GPIO
from pushbullet import PushBullet
import time
from time import strftime
import atexit
import urllib2
import config

def wait_for_internet_connection():
    print "waiting for connection"
    while True:
        try:
            response = urllib2.urlopen('http://64.233.168.101', timeout=1)
            print "connected"
            return
        except urllib2.URLError:
            print "no connection"
            pass

class Sensor:
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.lastval = -1
        self.opentime = 0
        self.closedtime = 0
        self.leftopenalarm = -1


print "starting, sleeping 10"
time.sleep(10)
print "slept"

wait_for_internet_connection()

sensors = []
for sensor in config.sensors:
    sensors.append(Sensor(sensor[0],sensor[1]))


for sensor in sensors:
    print "trying " + sensor.name + " on port " + "sensor.port"
    GPIO.setup(sensor.port, GPIO.IN)

pushers = []
for pusher_key in config.pb_keys:
    pushers.append(PushBullet(pusher_key))

messages = []
lastsend = 0
lastmessageAdd = 0


def sendPushes():
    global lastsend
    global messages
    global lastmessageAdd
    if time.time() - lastsend > 4 and len(messages) > 0 and (time.time() - lastmessageAdd > 4 or len(messages) == 1):
        print "sending"
        lastsend = time.time()
        sendthis = "\n".join(messages)
        messages = []
        title = "Home Alert"

        for pb in pushers:
            success, push = pb.push_note(title, sendthis)


def sendPush(title, message):
    print title
    global messages
    global lastmessageAdd
    messages.append(message)
    lastmessageAdd = time.time()
    sendPushes()


@atexit.register
def goodbye():
    sendPush('House monitoring stopping.', 'House monitoring stopping.')


i = 0

sendPush("System Startup " + strftime("%Y-%m-%d %H:%M:%S"), "SYSTEM STARTUP " + strftime("%Y-%m-%d %H:%M:%S"))
while 1 == 1:
    sendPushes()
    for sensor in sensors:
        val = GPIO.input(sensor.port)
        if val != sensor.lastval:
            print val
            i += 1
            extra = ''

            if val:
                sensor.opentime = time.time()
            elif sensor.opentime > 0:
                sensor.closedtime = time.time()
                elapsed = round(sensor.closedtime - sensor.opentime, 1)
                extra = " open for " + str(elapsed) + " seconds."

            openOrClosed = 'open' if val else 'closed'
            note = str(i) + " " + strftime(
                "%Y-%m-%d %H:%M:%S") + ' ' + sensor.name + " is " + openOrClosed + '.' + extra
            sendPush(note, note)
            sensor.lastval = val
            sensor.leftopenalarm = -1
        elif val and sensor.lastval and time.time() - sensor.opentime > 5 and round(time.time() - sensor.opentime,
                                                                                    0) != sensor.leftopenalarm and round(
                        time.time() - sensor.opentime, 0) % 60 == 0:
            sensor.leftopenalarm = round(time.time() - sensor.opentime, 0)
            note = sensor.name + " has been left open for " + str(round(time.time() - sensor.opentime,
                                                                        0)) + " seconds. Close the door, we aren't air conditioning the whole neighborhood."
            sendPush(note, note)
