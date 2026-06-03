import threading
import time


stop_event = threading.Event()


def worker():
    while not stop_event.is_set():
        print("running...")
        time.sleep(1)
    
    print("stop!")


thread = threading.Thread(target=worker)
thread.start()


#time.sleep(0)
stop_event.set()