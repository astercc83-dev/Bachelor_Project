import threading
import time


def my_task():
    print("بدأت الشغل")
    time.sleep(2)
    print("خلصت الشغل")


thread1 = threading.Thread(target=my_task)
thread1.start()
thread2 = threading.Thread(target=my_task)
thread2.start()

