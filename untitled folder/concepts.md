# Some Important concepts 

this file contains some important concepts about how to use the nidaqmx liberary

## Task()
 **Task means a measurement mission (i want to measure something)**
for example ‘‘‘Read from the channel AI0 , Use a speed rate 10 MS/s‘‘‘

- We can use it in Python like that:
```Python
import nidaqmx
''' the meaning of Task() here is make a new mission or new task,
but here is empty right now because we didn´t add any channel or configuration yet
  ''' 
with nidaqmx.Task() as Task:
  pass 
```

## Virtual Channel

**Is the name of the Channel inside the Programm**

## Physical Channel

a place in the hardware (body of PXI) like a pin or port or terminal, 
for example "Dev1/ai0" (Dev1: is the device name and ai0: channel name => Analog input 0)


