# Report: DAQ System Simulation
**Project:** Development of a Python-Based Interface for a PXI Data Acquisition System  
**Student:** Samir Elsherbiny  
**Supervisor:** Dr. Mohammad Amayreh  
**Date:** May 2026

---

## 1. Why Did We Build This Simulation?

Before getting access to the real PXI hardware, we built a complete simulation in Python.

The simulation answers one important question:

> **How can we read data from a very fast device (PXI), process it, and save it — all at the same time — without losing any data?**

---

## 2. The Three Building Blocks We Learned

### 2.1 Thread
- **What is it?** A thread is like a worker. You can have multiple workers doing different jobs at the same time inside the same program.
- **Library used:** `threading` (already built into Python, no installation needed)
- **Why do we need it?** Without threads, Python does one job, waits for it to finish, then does the next job. With threads, multiple jobs run at the same time.

```python
import threading

def my_task():
    print("I started working")

thread = threading.Thread(target=my_task)
thread.start()
```

---

### 2.2 Queue
- **What is it?** A Queue is a shared box between threads. One thread puts data in, another thread takes data out. It works like a queue at a supermarket — first in, first out (FIFO).
- **Library used:** `queue` (already built into Python)
- **Why do we need it?** Threads cannot safely share data directly. The Queue handles this safely without any conflicts.

```python
import queue

my_box = queue.Queue()
my_box.put("sample 0")   # put data in
data = my_box.get()       # take data out
```

---

### 2.3 Event
- **What is it?** A shared signal between threads. Think of it like a red flag. When the flag is raised, all threads know it is time to stop.
- **Three commands:**
  - `stop_event.set()` → raise the red flag (stop all threads)
  - `stop_event.is_set()` → is the red flag raised?
  - `stop_event.clear()` → lower the red flag (start again)

```python
stop_event = threading.Event()

# inside a thread:
while not stop_event.is_set():
    # keep working...

# from the main program:
stop_event.set()  # tell all threads to stop
```

---

## 3. The Main Problem: Buffer Overflow

### 3.1 What is a Buffer?
A buffer is a temporary storage area (like a bucket). The PXI card stores data in a buffer while Python reads it. If Python is too slow, the buffer fills up and new data overwrites old data. That old data is lost forever.

### 3.2 What is Buffer Overflow?
Buffer Overflow happens when the Reader is faster than the Processor.

```
Reader:    reads every 0.5 seconds  ← fast
Processor: processes every 1 second ← slow

Result: Queue fills up → Overflow → Data is lost!
```

### 3.3 How Did We Detect Buffer Overflow?
We used `queue.full()` to check before adding each new sample:

```python
if queue_1.full():
    lost_samples += 1
    print(f"Overflow! sample {i} is lost")
else:
    queue_1.put(f"sample {i}")
```

---

## 4. The Solution: Producer-Consumer Pattern

### 4.1 The Overall Structure
```
Reader Thread → Queue 1 → Processor Thread → Queue 2 → Saver Thread
     ↑                          ↑                           ↑
 stop_event                stop_event                   stop_event
```

### 4.2 What Each Thread Does

| Thread | Job | Speed |
|--------|-----|-------|
| Reader | Reads data and puts it in Queue 1 | Fast (0.5 sec) |
| Processor | Takes from Queue 1, processes, puts in Queue 2 | Slower (1 sec) |
| Saver | Takes from Queue 2 and saves to a file | Medium |

### 4.3 Why Do We Need a Queue Between Them?
Because the threads work at different speeds. The Queue works like a shock absorber — it holds the data safely while the Processor catches up. Without it, the Reader would have to wait for the Processor, and data would be lost.

### 4.4 Why Threading and Not Multiprocessing?
In our project, all three tasks (reading, processing, saving) are **I/O-bound** — they spend most of their time waiting (waiting for hardware, waiting to draw on screen, waiting to write to disk). Threading is perfect for I/O-bound tasks.

Multiprocessing would also require reconnecting to the PXI device in each process, which causes a gap in data acquisition and could damage the hardware. Ahmad Ahmad's thesis confirmed this same conclusion.

---

## 5. Problems We Faced and How We Solved Them

### Problem 1: The saved file was empty
**Why it happened:** Python collects data in memory (RAM) first and writes to disk later. If the program closes before Python writes, the file stays empty.  
**Solution:** Use `file.flush()` after every write to force Python to write immediately.

```python
file.write(data + "\n")
file.flush()  # write to disk right now!
```

---

### Problem 2: The Saver stopped too early
**Why it happened:** The Saver stopped as soon as `stop_event` was raised, even if Queue 2 still had data waiting to be saved.  
**Solution:** Change the while condition so the Saver keeps running until Queue 2 is completely empty.

```python
# Before (wrong):
while not stop_event.is_set():

# After (correct):
while not stop_event.is_set() or not queue_1.empty() or not queue_2.empty():
```

---

### Problem 3: The Processor stopped too early
**Why it happened:** Same as Problem 2. The Processor stopped before emptying Queue 1, leaving data stuck inside.  
**Solution:** Same fix — keep running until Queue 1 is empty.

```python
while not stop_event.is_set() or not queue_1.empty():
    try:
        data = queue_1.get(timeout=0.5)
        # process the data
    except:
        pass
```

---

### Problem 4: Data stuck in queues after shutdown
**Why it happened:** The main program was ending before the queues were fully emptied.  
**Solution:** After raising `stop_event`, wait for both queues to empty before closing the program.

```python
while not queue_1.empty():
    time.sleep(0.1)
while not queue_2.empty():
    time.sleep(0.1)
```

---

### Problem 5: Missing parentheses `()` on functions
**Why it happened:** Writing `queue.full` or `stop_event.is_set` without `()` means Python returns the function itself instead of running it. The result is always `True`, which breaks the logic completely.  
**Rule to remember:**

```python
# Wrong:
if queue_1.full:        ← always True! never runs the function
if stop_event.is_set:   ← always True! never runs the function

# Correct:
if queue_1.full():        ← runs the function, returns True or False
if stop_event.is_set():   ← runs the function, returns True or False
```

---

### Problem 6: Using a variable from outside inside a function
**Why it happened:** When we tried to change `lost_samples` inside a function, Python thought we were creating a new local variable, not changing the global one.  
**Solution:** Use the `global` keyword at the start of the function.

```python
lost_samples = 0  # defined outside

def reader():
    global lost_samples  # tell Python: use the one from outside!
    lost_samples += 1
```

---

## 6. The Final Complete Code

```python
import threading
import queue
import time

# Shared queues and variables
queue_1 = queue.Queue(maxsize=20)
queue_2 = queue.Queue()
stop_event = threading.Event()
lost_samples = 0
total_read = 0
total_processed = 0


def reader():
    """Reads data and puts it into Queue 1"""
    global lost_samples, total_read
    i = 0
    while not stop_event.is_set():
        if queue_1.full():
            lost_samples += 1
            print(f"Overflow - sample {i} lost. Total lost: {lost_samples}")
        else:
            queue_1.put(f"sample {i}")
            total_read += 1
            print(f"Reader: read sample {i}")
        i += 1
        time.sleep(0.5)


def processor():
    """Takes from Queue 1, processes, puts into Queue 2"""
    global total_processed
    while not stop_event.is_set() or not queue_1.empty():
        try:
            data = queue_1.get(timeout=0.5)
            total_processed += 1
            print(f"Processor: processing {data}")
            queue_2.put(data)
            time.sleep(1)
        except:
            pass


def saver():
    """Takes from Queue 2 and saves to file"""
    file = open("data.txt", "w")
    while not stop_event.is_set() or not queue_1.empty() or not queue_2.empty():
        try:
            data = queue_2.get(timeout=0.5)
            file.write(data + "\n")
            file.flush()
        except:
            pass
    file.close()
    print("Saver: file closed")


# Create and start all threads
thread_reader = threading.Thread(target=reader)
thread_processor = threading.Thread(target=processor)
thread_saver = threading.Thread(target=saver)

thread_reader.start()
thread_processor.start()
thread_saver.start()

# Wait for user to stop the program
input("Press Enter to stop...\n")
stop_event.set()

# Wait for queues to empty
while not queue_1.empty():
    time.sleep(0.1)
while not queue_2.empty():
    time.sleep(0.1)

# Wait for all threads to finish
thread_reader.join()
thread_processor.join()
thread_saver.join()

# Print final statistics
total_attempted = total_read + lost_samples
print(f"\n=== Final Results ===")
print(f"Total attempted:  {total_attempted}")
print(f"Total read:       {total_read}")
print(f"Total processed:  {total_processed}")
print(f"Total overflow:   {lost_samples}")
print(f"Check: {total_attempted} = {total_read} + {lost_samples} → {total_read + lost_samples == total_attempted}")
```

---

## 7. Results

When running the program with:
- **Reader:** every 0.5 seconds
- **Processor:** every 1 second
- **Queue 1:** max size 20 samples

| Situation | Result |
|-----------|--------|
| Reader faster than Processor | Overflow happens ❌ |
| Processor faster than Reader | No overflow ✅ |
| Larger Queue size | Delays overflow, does not prevent it |

---

## 8. Key Lessons Learned

1. **Multithreading is necessary** for high-speed data acquisition systems.
2. **The Queue** is the best way to safely pass data between threads.
3. **Buffer Overflow** happens when the Reader is faster than the Processor.
4. **Clean shutdown** requires waiting for all queues to empty before closing.
5. **Always use parentheses `()`** when calling any function in Python.
6. **Use `global`** when changing a variable that was defined outside a function.

---

## 9. Next Step: Connect to the Real PXI

The simulation is complete. When we get access to the PXI hardware, only one line needs to change in the Reader:

```python
# Simulation (now):
queue_1.put(f"sample {i}")

# Real PXI code (later):
data = task.read()
queue_1.put(data)
```

Everything else stays exactly the same. ✅
