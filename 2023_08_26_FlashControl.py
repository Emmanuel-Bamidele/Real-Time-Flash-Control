#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-------------------------------------------
           COPYRIGHT INFORMATION
-------------------------------------------

© 2023 Emmanuel Bamidele. All rights reserved.

This software and its documentation are protected by copyright law and international treaties. Unauthorized reproduction or distribution of this software, or any portion of it, may result in severe civil and criminal penalties, and will be prosecuted to the maximum extent possible under law.

Real-time Flash Experiment Control and Visualization software, including all related files, data, and documentation, are the intellectual property of Emmanuel Bamidele.

For questions, inquiries, and permissions related to the use and distribution of this software, please contact:

Emmanuel Bamidele
Email: correspondence.bamidele@gmail.com

-------------------------------------------
               LICENSE INFORMATION
-------------------------------------------

The Real-time Flash Experiment Control and Visualization software is released under the Apache License, Version 2.0. A copy of the license can be found in the LICENSE file on github or at:

https://www.apache.org/licenses/LICENSE-2.0

-------------------------------------------
              VERSION INFORMATION
-------------------------------------------

Real-time Flash Experiment Control and Visualization software
Version: 1.0
Date: August 2023

-------------------------------------------
                 DISCLAIMER
-------------------------------------------

The Real-time Flash Experiment Control and Visualization software is provided "as is" without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

The software is intended for research and educational purposes only. It is the responsibility of the user to ensure proper operation and adherence to all applicable laws and regulations while using this software.

-------------------------------------------
            CITATION INFORMATION
-------------------------------------------

To cite the Software Framework for Real-time Flash Control and Data Visualization, please use the following citation:

Bamidele, Emmanuel. (2023). Software Framework for Real-time Flash Control and Data Visualization [Software framework]. Retrieved from www.emmanuelbamidele.com

For the GitHub repository, visit:
https://github.com/Emmanuel-Bamidele/Real-Time-Flash-Control

Documentation is available on ResearchGate.

"""

import tkinter.messagebox
from tkinter import *
import webbrowser
from tkinter import filedialog, scrolledtext, messagebox
import time
import threading
import nidaqmx
import pyvisa
from matplotlib import pyplot as plt


# Functions for error handling

def display_error_messages(exception):
    """Display error message"""
    template = "Error: {0}. Arguments:\n{1!r}"
    message = template.format(type(exception).__name__, exception.args)
    messagebox.showinfo("Error", message)
    return


file_path = None


class AppRunModule:
    def try_to_start(self):
        try:
            initialize()
        except Exception as ex:
            display_error_messages(ex)
        return

    def run_all(self):
        try:
            self.try_to_start()
            reset_current()
            flash()
            reset_current()
            tkinter.messagebox.showinfo("Done", "Acquisition Finished!")
        except Exception as ex:
            display_error_messages(ex)
        return

    def stop_running(self):
        try:
            reset_current()
            f.close()
            exit()
        except Exception as ex:
            display_error_messages(ex)
            window.destroy()
        return


class PlotManager:
    def __init__(self, ax1, ax2, x_axis, pry_axis, sec_axis):
        # Axes for plotting
        self.ax1 = ax1
        self.ax2 = ax2

        # Variables for axis data
        self.x_axis1 = x_axis
        self.pry_axis1 = pry_axis
        self.sec_axis1 = sec_axis

        # Lists to store data points
        self.timeList = []
        self.VoltageList = []
        self.ResistanceList = []
        self.CurrentList = []
        self.CurrentDensityList = []
        self.TempList = []

        # Variables to store plotting parameters
        self.x = None
        self.xl = None
        self.y1 = None
        self.y1l = None
        self.y2 = None
        self.y2l = None

    def initialize_plots(self):
        self.x, _ = self.plot_strings(self.x_axis1.get())
        self.y1, _ = self.plot_strings(self.pry_axis1.get())
        self.y2, _ = self.plot_strings(self.sec_axis1.get())

        # Create initial plots with empty data
        self.line1, = self.ax1.plot([], [], color='blue', linewidth=3)
        self.line2, = self.ax2.plot([], [], color='red', linewidth=3)

    def update_plot_data(self):
        # Update the data of the existing plots
        self.line1.set_data(self.x, self.y1)
        self.line2.set_data(self.x, self.y2)

        # Adjust limits
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()

        # Refresh the plot
        plt.draw()

    def plot_strings(self, selected):
        mapping = {
            "Time (s)": (self.timeList, "Time ($s$)"),
            "Voltage (V)": (self.VoltageList, "Voltage ($V$)"),
            "Resistance (Ω)": (self.ResistanceList, "Resistance ($Ω$)"),
            "Current (A)": (self.CurrentList, "Current ($A$)"),
            "Current Density (A/mm2)": (self.CurrentDensityList, "Current Density ($A/mm2$)"),
            "Temperature (\N{DEGREE SIGN}C)": (self.TempList, "Temperature ($\N{DEGREE SIGN}C$)")
        }
        return mapping.get(selected, (None, None))

    def to_plot(self):
        x_get = self.x_axis1.get()
        self.x, self.xl = self.plot_strings(x_get)

        y1_get = self.pry_axis1.get()
        self.y1, self.y1l = self.plot_strings(y1_get)

        y2_get = self.sec_axis1.get()
        self.y2, self.y2l = self.plot_strings(y2_get)

        self.axis_plot()

    def axis_plot(self):
        title = f"{self.y1l} vs {self.y2l} Profiles"
        self.ax1.set_xlabel(self.xl, fontsize=18)
        self.ax1.set_title(title, fontsize=18)
        self.ax1.set_ylabel(self.y1l, color='blue', fontsize=18)
        self.ax1.tick_params(axis='y', labelcolor="blue")
        self.ax2.set_ylabel(self.y2l, color='red', fontsize=18)
        self.ax2.tick_params(axis='y', labelcolor="red")

        self.update_plot_data()


# Nidaq Task Management
class TaskManager:
    def __enter__(self):
        self.task = nidaqmx.Task()
        return self.task

    def __exit__(self, exc_type, exc_value, traceback):
        self.task.stop()
        self.task.close()


def initialize():
    global current_scale, temperature_channel, current_channel, voltage_channel, \
        daq_max_voltage, keithley_address, voltage_scale, pyrometer

    update_control()

    temperature_channel = str(t_channel.get())
    pyrometer = int(pyro.get())
    current_channel = str(I_channel.get())
    voltage_channel = str(v_channel.get())
    daq_max_voltage = int(Daq_voltage.get())
    PS_max_current = int(PS_current.get())
    PS_max_voltage = int(PS_voltage.get())
    keithley_address = str(Keithley_Address.get())
    current_scale = PS_max_current / daq_max_voltage
    voltage_scale = PS_max_voltage / daq_max_voltage


def do_nothing():
    return


def save_to():
    global file_path
    file_path = filedialog.askdirectory()
    if file_path:  # check if a path was actually selected
        folder_selected()
    return file_path


def folder_selected():
    folder_name = file_path.split('/')[-1]  # Get the last part of the path, which is the folder name.
    folder_select.config(text="Current Folder: " + folder_name)  # Change the button text.


def update_control():
    global current_limit, holding_time, current_density, current_rate, area, sampling_time, \
        timeList, VoltageList, ResistanceList, CurrentList, CurrentDensityList, TempList

    timeList = [0]
    VoltageList = [0]
    ResistanceList = [0]
    CurrentList = [0]
    CurrentDensityList = [0]
    TempList = [650]

    area = float(s_area.get())
    holding_time = float(hold_time.get())
    current_density = float(I_density.get())
    current_rate = float(I_rate.get())
    current_limit = current_density * area
    sampling_time = float(sampling_Time.get())

    error_message = validate_current_limit(current_limit)
    if error_message:
        I_limit.delete(0, END)
        I_limit.insert(END, f"\"{error_message}\"")
    else:
        I_limit.delete(0, END)
        I_limit.insert(END, str(round(current_limit, 3)))


def validate_current_limit(max_current):
    maximum_I = int(PS_current.get())
    if max_current > maximum_I:
        return f"Limit exceeded!"
    return


def control_update_thread():
    t1 = threading.Thread(target=update_control)
    t1.setDaemon(True)
    t1.start()
    return


def execution_time():
    total_time = (float(I_limit.get()) / current_rate) + holding_time
    return total_time


def write_current(time_now):
    with TaskManager() as task:
        task.ao_channels.add_ao_voltage_chan(current_channel, 'Channel-1', min_val=0, max_val=daq_max_voltage)
        task.start()
        current_value = (current_rate * time_now) if (current_rate * time_now) <= current_limit else current_limit
        task.write(current_value / current_scale)
    return current_value


def reset_current():
    with TaskManager() as task:
        task.ao_channels.add_ao_voltage_chan(current_channel, 'Channel-1', min_val=0, max_val=daq_max_voltage)
        task.start()
        task.write(0)


def read_voltage():
    with TaskManager() as task:
        task.ai_channels.add_ai_voltage_chan(voltage_channel, min_val=0, max_val=daq_max_voltage)
        task.start()
        raw_value = task.read()
        value = raw_value * voltage_scale
    return value


def read_temperature():
    with TaskManager() as task:
        task.ai_channels.add_ai_voltage_chan(temperature_channel, min_val=0, max_val=daq_max_voltage)
        task.start()
        temperature = task.read()
    return temperature


def flash():
    global ax1, ax2
    address = 'GPIB0::' + keithley_address + "::INSTR"
    multimeter = pyvisa.ResourceManager().open_resource(address, )
    multimeter.write(":ROUTe:CLOSe (@101)")
    multimeter.write(":SENSE:FUNCtion 'VOLTage'")

    write_data()
    Total_time = execution_time()
    startTime = time.time()

    fig, ax1 = plt.subplots(figsize=(8, 6))
    ax2 = ax1.twinx()
    plot_manager = PlotManager(ax1, ax2, x_axis1, pry_axis1, sec_axis1)
    plot_manager.initialize_plots()
    plot_manager.to_plot()

    while float(time.time() - startTime) <= Total_time:
        # write, compute and read data
        time_now = float(time.time() - startTime)
        current_in = write_current(time_now)
        PS_voltage_value = read_voltage()
        temp_value = read_temperature()
        voltage_value1 = float(multimeter.query(':SENSE:DATA:FRESh?'))  # .split(',')[0][:-2])
        voltage_value = 0.00 if current_in == 0 else abs(voltage_value1)
        resistance_value = voltage_value / current_in
        current_densityJ = current_in / area

        # Using plot manager to store the data for real-time plotting
        plot_manager.timeList.append(time_now)
        plot_manager.CurrentList.append(current_in)
        plot_manager.VoltageList.append(voltage_value)
        plot_manager.ResistanceList.append(resistance_value)
        plot_manager.CurrentDensityList.append(current_densityJ)
        plot_manager.TempList.append(temp_value * 230 + pyrometer)

        # show and save data
        screen_output(time_now, voltage_value, resistance_value, current_in, current_densityJ, (
                temp_value * 230 + pyrometer))
        f.write(
            str(time.time() - startTime) + '\t' + str(abs(current_in)) + "\t" + str(current_densityJ) + "\t" + str(
                abs(voltage_value)) + '\t' + str(abs(PS_voltage_value)) + '\t' + str(
                resistance_value) + '\t' + str(temp_value * 230 + pyrometer) + "\n")

        # plot live data
        plot_manager.to_plot()
        fig.tight_layout()
        plt.pause(0.01)
        time.sleep(sampling_time)
        Total_time = execution_time()

    f.close()
    return


def write_data():
    global f
    if file_path is None:
        messagebox.showerror("Error", "Please select a folder first!")
        return
    file_name1 = str(file_name.get())
    f_name = file_path + "\\" + file_name1 + '.csv'
    f = open(f_name, "w")
    f.write("Time\tCurrent\tCurrent Density\tVoltage(Keithley)\tVoltage(Power Supply)\tResistance\tTemperature\n")
    f.write("s\tA\tA/mm2\tV\tV\tohms\t\N{DEGREE SIGN}C\n")
    f.write(f"0\t0\t0\t0\t0\t0\t{str(pyrometer)}\n")


def screen_output(time_in, voltage1, resistance1, current_in, current_dense, temp):
    time_output.delete(0, END)
    time_output.insert(END, str(round(time_in, 3)))
    voltage_output.delete(0, END)
    voltage_output.insert(END, str(round(voltage1, 5)))
    resistance_output.delete(0, END)
    resistance_output.insert(END, str(round(resistance1, 5)))
    I_output.delete(0, END)
    I_output.insert(END, str(round(current_in, 3)))
    I_dens_output.delete(0, END)
    I_dens_output.insert(END, str(round(current_dense, 3)))
    temp_output.delete(0, END)
    temp_output.insert(END, str(round(temp, 3)))
    return


window = Tk()
window.geometry("700x350")

window.title("© Emmanuel Bamidele 2023")


# window.iconbitmap(
# r"C:\Users\AMI\Desktop\Emmanuel\Codes\Flash-Sintering-Software-Logo.ico")


def callback(url):
    webbrowser.open_new_tab(url)


Program_name1 = Label(window, font=('Verdana', 12, 'bold'), text='FLASH - CURRENT CONTROL', fg='blue')
Program_name1.place(relx=.25, rely=.005)

Program_info2 = Label(window, font=('Verdana', 7), text='Source Code', fg='blue', cursor="hand2")
Program_info2.place(relx=.8, rely=.01)
Program_info2.bind("<Button-1>", lambda e: callback("https://github.com/Emmanuel-Bamidele/Real-Time-Flash-Control"))

app = AppRunModule()
# Hardware
channel_label = Label(window, text="Interfacing Parameters", font=('Copperplate Gothic', 10))
channel_label.place(relx=.02, rely=.1)

channel_label2 = Label(window, text="(Documentation)", font=('Copperplate Gothic', 10), fg='blue',
                       cursor="hand2")
channel_label2.place(relx=.02, rely=.16)
channel_label2.bind("<Button-1>", lambda e: callback("https://github.com/Emmanuel-Bamidele/Real-Time-Flash-Control"))

t_channel_label = Label(window, text="Temp. Channel", font=('Copperplate Gothic', 8))
t_channel_label.place(relx=.02, rely=.23)

t_channel = Entry(window, width=10)
t_channel.insert(END, 'Dev1/ai2')
t_channel.place(relx=.02, rely=.29)

pyro_label = Label(window, text="Pyro Min Temp", font=('Copperplate Gothic', 8))
pyro_label.place(relx=.16, rely=.23)

pyro = Entry(window, width=10)
pyro.insert(END, '650')
pyro.place(relx=.16, rely=.29)

I_channel_label = Label(window, text="Current Channel", font=('Copperplate Gothic', 8))
I_channel_label.place(relx=.02, rely=.36)

I_channel = Entry(window, width=10)
I_channel.insert(END, 'Dev1/ao1')
I_channel.place(relx=.02, rely=.42)

PS_current_label = Label(window, text="PS Max Current", font=('Copperplate Gothic', 8))
PS_current_label.place(relx=.16, rely=.36)

PS_current = Entry(window, width=10)
PS_current.insert(END, "100")
PS_current.place(relx=.16, rely=.42)

v_channel_label = Label(window, text="Voltage Channel", font=('Copperplate Gothic', 8))
v_channel_label.place(relx=.02, rely=.49)

v_channel = Entry(window, width=10)
v_channel.insert(END, 'Dev1/ai0')
v_channel.place(relx=.02, rely=.55)

PS_voltage_label = Label(window, text="PS Max Voltage", font=('Copperplate Gothic', 8))
PS_voltage_label.place(relx=.16, rely=.49)

PS_voltage = Entry(window, width=10)
PS_voltage.insert(END, "30")
PS_voltage.place(relx=.16, rely=.55)

Keithley_Address_label = Label(window, text="Keithley Address", font=('Copperplate Gothic', 8))
Keithley_Address_label.place(relx=.02, rely=.62)

Keithley_Address = Entry(window, width=10)
Keithley_Address.insert(END, '13')
Keithley_Address.place(relx=.02, rely=.68)

Daq_voltage_label = Label(window, text="DAQ Max Volts", font=('Copperplate Gothic', 8))
Daq_voltage_label.place(relx=.16, rely=.62)

Daq_voltage = Entry(window, width=10)
Daq_voltage.insert(END, '10')
Daq_voltage.place(relx=.16, rely=.68)

file_name_label = Label(window, text="File Name", font=('Copperplate Gothic', 10))
file_name_label.place(relx=.02, rely=.75)

file_name = Entry(window, width=25)
file_name.insert(END, time.strftime("%Y_%m_%d-%I-%M-%p-"))
file_name.place(relx=.02, rely=.81)

folder_select = Button(window, text="Choose Folder", command=save_to, bg="red", fg='black')
folder_select.place(relx=.02, rely=.89)

# Parameters
area_label = Label(window, text="Area (mm2)", font=('Copperplate Gothic', 10), fg='blue')
area_label.place(relx=.3, rely=.1)

s_area = Entry(window, fg="blue")
s_area.insert(END, "0.00")
s_area.place(relx=.3, rely=.16)

I_density_label = Label(window, text="Current Density (A/mm2)", font=('Copperplate Gothic', 10), fg='blue')
I_density_label.place(relx=.3, rely=.23)

I_density = Entry(window, fg="blue")
I_density.insert(END, "0.00")
I_density.place(relx=.3, rely=.29)

I_limit_label = Label(window, text="Current Limit (A)", font=('Copperplate Gothic', 10), fg='blue')
I_limit_label.place(relx=.3, rely=.36)

I_limit = Entry(window, fg="red")
I_limit.insert(END, "auto-calculated")
I_limit.place(relx=.3, rely=.42)

I_rate_label = Label(window, text="Current Rate (A/s)", font=('Copperplate Gothic', 10), fg='blue')
I_rate_label.place(relx=.3, rely=.49)

I_rate = Entry(window, fg="blue")
I_rate.insert(END, "0.00")
I_rate.place(relx=.3, rely=.55)

hold_time_label = Label(window, text="Holding Time (s)", font=('Copperplate Gothic', 10), fg='blue')
hold_time_label.place(relx=.3, rely=.62)

hold_time = Entry(window, fg="blue")
hold_time.insert(END, "0.00")
hold_time.place(relx=.3, rely=.68)

sampling_Time_label = Label(window, text="Sampling Freq (s^-1)", font=('Copperplate Gothic', 10), fg='blue')
sampling_Time_label.place(relx=.3, rely=.75)

sampling_Time = Entry(window, fg='blue')
sampling_Time.insert(END, "0.01")
sampling_Time.place(relx=.3, rely=.81)

Update_Control = Button(window, text="Update Control", command=control_update_thread,
                        bg='black', fg='white')  # link this to the function
Update_Control.place(relx=.3, rely=.89)

# live plot option
x_axis1 = StringVar(window)
pry_axis1 = StringVar(window)
sec_axis1 = StringVar(window)
x_axis1.set("Time (s)")
pry_axis1.set("Voltage (V)")
sec_axis1.set("Current (A)")

x_options = ["Time (s)", "Temperature (\N{DEGREE SIGN}C)", "Current Density (A/mm2)"]
y_options = ["Voltage (V)", "Current (A)", "Temperature (\N{DEGREE SIGN}C)", "Resistance (Ω)",
             "Current Density (A/mm2)"]

x_axis_label = Label(window, text="Live Plot (x-axis)", font=('Copperplate Gothic', 10), fg='blue')
x_axis_label.place(relx=.55, rely=.1)
x_axis = OptionMenu(window, x_axis1, *x_options)
x_axis.place(relx=.55, rely=.16)

pry_axis_label = Label(window, text="Primary Axis", font=('Copperplate Gothic', 10), fg='blue')
pry_axis_label.place(relx=.55, rely=.36)
pry_axis = OptionMenu(window, pry_axis1, *y_options)
pry_axis.place(relx=.55, rely=.42)

sec_axis_label = Label(window, text="Secondary Axis", font=('Copperplate Gothic', 10), fg='blue')
sec_axis_label.place(relx=.55, rely=.62)
sec_axis = OptionMenu(window, sec_axis1, *y_options)
sec_axis.place(relx=.55, rely=.68)

# Screen
time_output_label = Label(window, text="Time(s)", font=('Copperplate Gothic', 10), fg='red')
time_output_label.place(relx=.75, rely=.1)

time_output = Entry(window, fg="red")
time_output.insert(END, "0.00")
time_output.place(relx=.75, rely=.16)

I_dens_output_label = Label(window, text="Current Density (A/mm2)", font=('Copperplate Gothic', 10), fg='red')
I_dens_output_label.place(relx=.75, rely=.23)

I_dens_output = Entry(window, fg="red")
I_dens_output.insert(END, "0.00")
I_dens_output.place(relx=.75, rely=.29)

voltage_output_label = Label(window, text="Voltage (V)", font=('Copperplate Gothic', 10), fg='red')
voltage_output_label.place(relx=.75, rely=.36)

voltage_output = Entry(window, fg="red")
voltage_output.insert(END, "0.00")
voltage_output.place(relx=.75, rely=.42)

I_output_label = Label(window, text="Current (A)", font=('Copperplate Gothic', 10), fg='red')
I_output_label.place(relx=.75, rely=.49)

I_output = Entry(window, fg="red")
I_output.insert(END, "0.00")
I_output.place(relx=.75, rely=.55)

temp_output_label = Label(window, text="Temperature (\N{DEGREE SIGN}C)", font=('Copperplate Gothic', 10), fg='red')
temp_output_label.place(relx=.75, rely=.62)

temp_output = Entry(window, fg="red")
temp_output.insert(END, "650")
temp_output.place(relx=.75, rely=.68)

resistance_output_label = Label(window, text="Resistance (Ω)", font=('Copperplate Gothic', 10), fg='red')
resistance_output_label.place(relx=.75, rely=.75)

resistance_output = Entry(window, fg="red")
resistance_output.insert(END, "0.00")
resistance_output.place(relx=.75, rely=.81)

Start_Acquisition = Button(window, text="Start", command=app.run_all, bg="green",
                           fg='white')  # link this to the function
Start_Acquisition.place(relx=.75, rely=.89)

Stop_Acquisition = Button(window, text="Stop", command=app.stop_running, bg="red",
                          fg='white')  # link this to the function
Stop_Acquisition.place(relx=.86, rely=.89)

window.mainloop()
