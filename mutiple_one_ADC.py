import nidaqmx

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0:7")
    print(task.timing.samp_clk_max_rate)


# Get the product type of the device

system = nidaqmx.system.System.local()

for device in system.devices:
    print(device.name, device.product_type)