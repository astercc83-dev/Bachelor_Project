import threading
import queue
import time


my_box = queue.Queue()

def producer():
    for i in range(5):
        my_box.put(f"طوبة {i}")
        print(f"المُنتج: حطيت طوبة {i}")
        time.sleep(1)


def consumer():
    for i in range(5):
        brick = my_box.get()
        print(f"المُستهلك: أخدت {brick}")
        time.sleep(2)


thread_producer = threading.Thread(target=producer)
thread_consumer = threading.Thread(target=consumer)

thread_producer.start()
thread_consumer.start()
