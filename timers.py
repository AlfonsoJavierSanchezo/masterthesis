
from threading import Timer
import time
import random

timers=[]

def idle(msg):
    print("****Received: "+ str(msg))
    timers[msg]=Timer(5,idle,[msg]).start()


if __name__ == '__main__':

    for i in range(6):
        timers.append(Timer(5,idle,[i]))
        timers[i].start()
        print(type(timers[i]))
    while True:
        rand= random.randint(0,5)
        print(rand)
        timers[rand].cancel()
        timers[rand]=Timer(5,idle,[rand])
        timers[rand].start()
        print("****Reset :"+str(rand))
        time.sleep(1)

