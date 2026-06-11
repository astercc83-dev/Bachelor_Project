"""
================================================================
  Flow-Rate Calculation for the Apexelektrode (TUE Project)
================================================================

  What this program does:
  -----------------------
  1. The Alluris FMI force gauge runs the experiment and saves
     the data into an Excel file (Time + Force).
  2. This program OPENS that Excel file.
  3. It calculates the flow rate (ml/min).
  4. It says if the tube is OK (>= 2.5 ml/min).
  5. It draws a simple plot and saves a result Excel file.

  We do NOT read live from the device.
  We only read the Excel file the device already created.

  Libraries needed (install once):
     pip install pandas matplotlib openpyxl
================================================================
"""

import pandas as pd                 # to read and write Excel files
import matplotlib.pyplot as plt     # to draw the plot


# ----------------------------------------------------------------
# Fixed values we need everywhere
# ----------------------------------------------------------------
GRAVITATION = 9.81        # m/s^2  -> turns force (N) into weight
WATER_DENSITY = 1.0       # g/ml   -> 1 gram of water = 1 milliliter
TARGET_FLOW = 2.5         # ml/min -> the minimum we need


# ================================================================
# STEP 1: Read the Excel file that the device saved
# ================================================================
def read_excel(filename):
    """
    Opens the Excel file from the Alluris device.
    Returns two lists: the times and the forces.

    IMPORTANT: the Excel must have two columns:
       Column 1 = time in seconds
       Column 2 = force in Newton
    """
    # Read the whole Excel file into a table
    table = pd.read_excel(filename)

    # Take the first column as time, the second column as force
    times = table.iloc[:, 0].tolist()    # iloc[:, 0] = all rows, column 0
    forces = table.iloc[:, 1].tolist()   # iloc[:, 1] = all rows, column 1

    print(f"Read {len(times)} values from '{filename}'")
    return times, forces


# ================================================================
# STEP 2: Calculate the flow rate from the forces
# ================================================================
def calculate_flow_rate(times, forces):
    """
    Turns the measured force into a flow rate.

    Idea:
      Force (N)  -> Weight (g)   ->  Volume (ml)  ->  divide by time
    """
    # The first and last force, turned into weight (grams)
    weight_start = (forces[0] / GRAVITATION) * 1000    # N -> g
    weight_end = (forces[-1] / GRAVITATION) * 1000

    # How much water was collected (in ml). 1 g water = 1 ml
    volume_ml = (weight_end - weight_start) / WATER_DENSITY

    # How much time passed (turn seconds into minutes)
    time_min = (times[-1] - times[0]) / 60.0

    # Flow rate = how much water per minute
    flow_rate = volume_ml / time_min

    return round(flow_rate, 2)


# ================================================================
# STEP 3: Say if the tube is good enough
# ================================================================
def check_result(flow_rate):
    """
    Compares the flow rate with the target (2.5 ml/min).
    Prints OK or TOO LOW.
    """
    if flow_rate >= TARGET_FLOW:
        print(f"Flow rate = {flow_rate} ml/min  -->  OK (tube is good)")
    else:
        print(f"Flow rate = {flow_rate} ml/min  -->  TOO LOW (tube not good)")


# ================================================================
# STEP 4: Draw a simple plot
# ================================================================
def make_plot(times, forces):
    """
    Draws the force over time, so we can SEE the line rising.
    Saves the picture as 'plot.png'.
    """
    plt.plot(times, forces)
    plt.xlabel("Time [s]")
    plt.ylabel("Force [N]")
    plt.title("Flow-Rate Measurement")
    plt.grid(True)
    plt.savefig("plot.png")          # save the picture
    plt.show()                       # show it on screen
    print("Plot saved as 'plot.png'")


# ================================================================
# STEP 5: Save the result into a new Excel file (for colleagues)
# ================================================================
def save_result(flow_rate, filename="result.xlsx"):
    """
    Makes a small Excel file with the final result.
    Colleagues who don't use Python can open and read it.
    """
    # Decide the text for the result
    if flow_rate >= TARGET_FLOW:
        verdict = "OK"
    else:
        verdict = "TOO LOW"

    # Build a small table with the result
    result_table = pd.DataFrame({
        "Flow rate (ml/min)": [flow_rate],
        "Target (ml/min)": [TARGET_FLOW],
        "Result": [verdict],
    })

    # Save the table as an Excel file
    result_table.to_excel(filename, index=False)
    print(f"Result saved as '{filename}'")


# ================================================================
# MAIN PROGRAM: run all steps, one after the other
# ================================================================
# Change this name to the real Excel file from the device:
EXCEL_FILE = "device_data.xlsx"

# Step 1: read the data
times, forces = read_excel(EXCEL_FILE)

# Step 2: calculate the flow rate
flow = calculate_flow_rate(times, forces)

# Step 3: check if it is OK
check_result(flow)

# Step 4: draw the plot
make_plot(times, forces)

# Step 5: save the result Excel
save_result(flow)
