###############################
#
# UI control system designed to manage all inputs and outputs of a custom electrolyzer system
# Made by Ryan Greene, 2025
#
###############################

#Import QT libraries
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QDoubleValidator, QPixmap

#Import basic libraries
from decimal import Decimal
from pid_control import heater
import nidaqmx
import time
import pyvisa
import re
import sys
import os
import pandas as pd
import serial
from minimalmodbus import NoResponseError

device_list = {
    "Pump Digital": "Dev1/port0/line15",
    "Pump Analog": "cDAQ1Mod1/ao3",
    "Water Meter": "Dev1/ai6"
}

#Globally define power supply and pump serial address
rm = pyvisa.ResourceManager()
try:
    instr = rm.open_resource("GPIB::8::INSTR")
except pyvisa.errors.VisaIOError:
    sys.exit("Error: Power supply not connected.")
pump_port = "COM1"

devices = {
    "Water Resist": "Dev1/ai6"
}

#PID heat control connection check
controller = heater.OmegaPID('COM7', 247)
try:
    controller.status_check()
except NoResponseError:
    sys.exit("Error: Heat controller disconnected or on incorrect port.")
cell = heater.DeltaPID('COM6', 1)
if cell.serial is None:
    raise ValueError("Instrument.serial is none")
cell.serial.baudrate = 19200

#Tasks for controlling the pump
def pump_start_stop():
    pump_start_task = nidaqmx.Task(new_task_name="Pump Start")
    pump_start_task.do_channels.add_do_chan(device_list["Pump Digital"])
    return pump_start_task

def pump_flow():
    pump_flow_task = nidaqmx.Task(new_task_name="Flow Set")
    pump_flow_task.ao_channels.add_ao_voltage_chan(device_list["Pump Analog"], min_val=0.0, max_val=10.0)
    return pump_flow_task

#Defining the main UI window
class UI_Setup(QMainWindow):

    #Initialize the main UI. Construct main UI window, graphics of system process flow, and settings for all controlled variables.
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Electrolyzer Monitor")
        self.base = QtWidgets.QWidget()
        self.base.setObjectName("baseWidget")
        self.setCentralWidget(self.base)
        self.move(100, 100)
        #Construct base layout for window
        layout = QtWidgets.QVBoxLayout()
        self.base.setLayout(layout)
        pixmap = QPixmap("C:/Users/Ryan/Documents/Electrolyzer/GUI/UI_v4/elec_back6.png")

        #Create graphical depiction of system layout
        self.diagram = QtWidgets.QLabel()
        self.diagram.setPixmap(pixmap)

        #Construct font for graphical labels
        label_font = QtGui.QFont()
        label_font.setPointSize(16)

        #Oxygen measurement labels and values
        self.liquid_lvl_1 = QtWidgets.QLabel("Liquid Level (mL)", self.diagram)
        self.liquid_lvl_1.setFont(label_font)
        self.liquid_lvl_1.setGeometry(7, 250, 260, 40)

        self.pressure_1 = QtWidgets.QLabel("O\N{SUBSCRIPT TWO} Pressure (psi)", self.diagram)
        self.pressure_1.setFont(label_font)
        self.pressure_1.setGeometry(7, 284, 260, 40)

        self.temp_1 = QtWidgets.QLabel("Temperature (°C)", self.diagram)
        self.temp_1.setFont(label_font)
        self.temp_1.setGeometry(7, 318, 260, 40)

        self.liquid_val_1 = QtWidgets.QLabel("Test", parent=self.diagram)
        self.liquid_val_1.setFont(label_font)
        self.liquid_val_1.setGeometry(205, 250, 260, 40)

        self.pressure_val_1 = QtWidgets.QLabel("Test", parent=self.diagram)
        self.pressure_val_1.setFont(label_font)
        self.pressure_val_1.setGeometry(205, 284, 260, 40)

        self.temp_val_1 = QtWidgets.QLabel(parent=self.diagram)
        self.temp_val_1.setFont(label_font)
        self.temp_val_1.setGeometry(205, 318, 260, 40)

        #Hydrogen measurement labels and values
        self.liquid_lvl_2 = QtWidgets.QLabel("Liquid Level (mL)", self.diagram)
        self.liquid_lvl_2.setFont(label_font)
        self.liquid_lvl_2.setGeometry(924, 272, 260, 40)

        self.pressure_2 = QtWidgets.QLabel("H\N{SUBSCRIPT TWO} Pressure (psi)", self.diagram)
        self.pressure_2.setFont(label_font)
        self.pressure_2.setGeometry(924, 307, 260, 40)

        self.temp_2 = QtWidgets.QLabel("Temperature (°C)", self.diagram)
        self.temp_2.setFont(label_font)
        self.temp_2.setGeometry(924, 343, 260, 40)

        self.liquid_val_2 = QtWidgets.QLabel("Test", parent=self.diagram)
        self.liquid_val_2.setFont(label_font)
        self.liquid_val_2.setGeometry(1119, 272, 260, 40)

        self.pressure_val_2 = QtWidgets.QLabel("Test", parent=self.diagram)
        self.pressure_val_2.setFont(label_font)
        self.pressure_val_2.setGeometry(1119, 307, 260, 40)

        self.temp_val_2 = QtWidgets.QLabel("Test", parent=self.diagram)
        self.temp_val_2.setFont(label_font)
        self.temp_val_2.setGeometry(1119, 343, 260, 40)

        #Water conductivity measurement
        self.flow_rate = QtWidgets.QLabel("Flow Rate (mL/min)", self.diagram)
        self.flow_rate.setFont(label_font)
        self.flow_rate.setGeometry(7, 421, 260, 40)

        self.resist = QtWidgets.QLabel("Resistivity (MΩ)", self.diagram)
        self.resist.setFont(label_font)
        self.resist.setGeometry(7, 464, 260, 40)

        self.flow_val = QtWidgets.QLabel("0.00", parent=self.diagram)
        self.flow_val.setFont(label_font)
        self.flow_val.setGeometry(205, 421, 260, 40)

        self.resist_val = QtWidgets.QLabel(parent=self.diagram)
        self.resist_val.setFont(label_font)
        self.resist_val.setGeometry(205, 464, 260, 40)

        #General function buttons
        self.commit_btn = QtWidgets.QPushButton("Commit Settings")
        self.commit_btn.clicked.connect(self.commit_btn_clicked)

        self.term_btn = QtWidgets.QPushButton("Terminate Program")
        self.term_btn.setEnabled(False)
        self.term_btn.clicked.connect(self.term_btn_clicked)

        #Tabs containing settings
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self.elec_UI(), "Power Control")
        self.tabs.addTab(self.pump_ui(), "Flow Control")
        self.tabs.addTab(self.temp_ui(), 'Temperature Control')

        #Adding all widgets to the base layout
        layout.addWidget(self.diagram)
        layout.addWidget(self.tabs)
        layout.addWidget(self.commit_btn)
        layout.addWidget(self.term_btn)

        #Dict for storing settings during operation
        self.settings = {
            'Voltage': 0.00,
            'Current': 0.00,
            'Flow': 0.00,
            'Temp': 0.00
            }

        #System state variable for logging purposes
        self.Running = 'Standby'

    #Tabs pertaining to power supply control
    def elec_UI(self):
        elec_tab = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        layout.setColumnMinimumWidth(2, 5)
        
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(75)

        #Text labels
        self.V_Text = QtWidgets.QLabel("Voltage (V)")
        self.V_Text.setFont(font)
        self.V_Text.setObjectName("V_Text")
        layout.addWidget(self.V_Text, 0, 0)

        self.I_Text = QtWidgets.QLabel("Current (mA)")
        self.I_Text.setFont(font)
        self.I_Text.setObjectName("I_Text")
        layout.addWidget(self.I_Text, 0, 1)

        #Space to enter settings before writing to power supply
        self.V_Write = QtWidgets.QLineEdit()
        self.V_Validate = QDoubleValidator(0.000, 61.425, 3)
        self.V_Validate.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.V_Write.setValidator(self.V_Validate)
        self.V_Write.setFont(font)
        self.V_Write.setObjectName("V_Write")
        self.V_Write.setPlaceholderText("0.00 V")
        layout.addWidget(self.V_Write, 1, 0)

        self.I_Write = QtWidgets.QLineEdit()
        self.I_Validate = QDoubleValidator(0.000, 1000.000, 3)
        self.I_Validate.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.I_Write.setValidator(self.I_Validate)
        self.I_Write.setFont(font)
        self.I_Write.setObjectName("I_Write")
        self.I_Write.setPlaceholderText("0.00 mA")
        layout.addWidget(self.I_Write, 1, 1)

        #Measurement of current power supply output
        self.V_Read = QtWidgets.QLabel()
        self.V_Read.setFont(font)
        self.V_Read.setObjectName("V_Read")
        layout.addWidget(self.V_Read, 2, 0)

        self.I_Read = QtWidgets.QLabel()
        self.I_Read.setFont(font)
        self.I_Read.setObjectName("I_Read")
        layout.addWidget(self.I_Read, 2, 1)

        #Measurement to determine power output
        self.Power = QtWidgets.QLabel("Power (W)")
        self.Power.setFont(font)
        self.Power.setObjectName("Power")
        layout.addWidget(self.Power, 0, 3)

        self.Power_Calc = QtWidgets.QLabel()
        self.Power_Calc.setFont(font)
        self.Power_Calc.setObjectName("Power_Calc")
        layout.addWidget(self.Power_Calc, 1, 3)

        elec_tab.setLayout(layout)
        return elec_tab
    
    #Tab pertaining to flow control settings
    def pump_ui(self):
        pump_tab = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(75)

        #Flow control settings entered before instrument write
        self.Flow_Text = QtWidgets.QLabel("Flow Rate (mL/min)")
        self.Flow_Text.setFont(font)
        layout.addWidget(self.Flow_Text, 0, 0)

        self.Flow_Write = QtWidgets.QLineEdit()
        self.Flow_Validate = QDoubleValidator(0.00, 2000.00, 2)
        self.Flow_Validate.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.Flow_Write.setValidator(self.Flow_Validate)
        self.Flow_Write.setFont(font)
        self.Flow_Write.setPlaceholderText("0.00 mL/min")
        layout.addWidget(self.Flow_Write, 1, 0)

        #Emergency flow stop button
        self.Flow_Stop = QtWidgets.QPushButton("Stop Flow")
        self.Flow_Stop.clicked.connect(self.stop_flow)
        layout.addWidget(self.Flow_Stop, 2, 0)

        pump_tab.setLayout(layout)
        return(pump_tab)
    
    #Tab pertaining to PID temperature control
    def temp_ui(self):
        temp_tab = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(75)

        #Temperature measurement settings before instrument write
        self.Temp_Text = QtWidgets.QLabel("Temperature (°C)")
        self.Temp_Text.setFont(font)
        layout.addWidget(self.Temp_Text, 0, 0)

        self.Temp_Set = QtWidgets.QLineEdit()
        self.Temp_Validate = QDoubleValidator(0.00, 100.00, 2)
        self.Temp_Validate.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.Temp_Set.setValidator(self.Temp_Validate)
        self.Temp_Set.setFont(font)
        self.Temp_Set.setPlaceholderText('0.00 °C')
        layout.addWidget(self.Temp_Set, 1, 0)

        temp_tab.setLayout(layout)
        return(temp_tab)

    #This slot triggers when settings are committed. 
    #Writes all settings to instruments, pulling from settings dictionary if an empty string is detected in the corresponding text field.
    def commit_btn_clicked(self):
        self.Running = 'Initialization'
        timer_2.setInterval(5 * 1000)

        #Writing voltage to power supply
        v = self.V_Write.text()
        if v == "" and self.V_Write.placeholderText() == "0.00 V":
            pass
        elif v == "":
            instr.write('VSET' + str(self.settings['Voltage']))
        else:
            try:
                v_f = float(v)
                self.settings['Voltage'] = v_f
                instr.write('VSET ' + str(self.settings['Voltage']))
                self.V_Write.setPlaceholderText(self.V_Write.text() + " V")
            except ValueError:
                print('Invalid Entry')
        self.V_Write.clear()

        #Writing current to power supply
        s = self.I_Write.text()
        if s == "" and self.I_Write.placeholderText() == "0.00 mA":
            pass
        elif s == "":
            instr.write('ISET' + str(self.settings['Current']) + ' MA')
        else:
            try:
                s_f = float(s)
                self.settings['Current'] = s_f
                instr.write('ISET ' + str(self.settings['Current']) + ' MA')
                self.I_Write.setPlaceholderText(self.I_Write.text() + " mA")
            except ValueError:
                print("Invalid Entry")
        self.I_Write.clear()

        #Writing flow rate to pump
        f = self.Flow_Write.text()
        if f == "" and self.Flow_Write.placeholderText() == "0.00 mL/min":
            pass
        elif f == "":
            set_rate.write(self.settings['Flow'] / 60)
            pump_on.write(False)
            self.flow_val.setText(str(self.settings['Flow']))
        else:
            try:
                f_f = float(f)
                set_rate.write(f_f / 60)
                if f_f == 0:
                    pass
                else:
                    pump_on.write(False)
                self.Flow_Write.setPlaceholderText(self.Flow_Write.text() + " mL/min")
                self.flow_val.setText(self.Flow_Write.text())
                self.settings['Flow'] = int(self.Flow_Write.text())
            except ValueError:
                print("Invalid Entry")
        self.Flow_Write.clear()

        #Writing temperature set point to PID
        t = self.Temp_Set.text()
        if t == "" and self.Temp_Set.placeholderText() == "0.00 °C":
            pass
        elif t == "":
            controller.set_sp_loop1(self.settings['Temp'])
        else:
            try:
                t_f = float(t)
                self.settings['Temp'] = t_f
                controller.set_sp_loop1(self.settings['Temp'])
                cell.set_sp(int(self.settings['Temp']) * 10)
                self.Temp_Set.setPlaceholderText(str(self.settings['Temp']) + ' °C')
            except ValueError:
                print('Invalid Entry')
        self.Temp_Set.clear()

        if self.term_btn.isEnabled():
            pass
        else:
            #init_check = QtCore.QTimer()
            #init_check.setSingleShot(True)
            #init_check.timeout.connect(self.system_check)
            #init_check.start(120 * 1000)
            self.term_btn.setEnabled(True)

    #This slot triggers when the termination button is clicked.
    #All instruments are set to 0, the logging timer returns to standby, and the commit button is enabled again.
    def term_btn_clicked(self):
        self.Running = 0
        timer_2.setInterval(300 * 1000)
        instr.write('VSET 0')
        instr.write('ISET 0')
        set_rate.write(0)
        pump_on.write(True)
        controller.set_sp_loop1(0)

        self.Running = 'Standby'
        self.term_btn.setEnabled(False)
        self.commit_btn.setEnabled(True)

    #This slot triggers when the flow stop button is pressed. Immediately stops pump flow.
    def stop_flow(self):
        set_rate.write(0)
        pump_on.write(True)
    
    #def system_check(self):
        #check if levels are good before initializing system

    #This slot triggers when the program is closed. All instruments are set to zero and the timers are disabled.
    def closeEvent(self, event):
        timer_1.stop()
        timer_2.stop()
        instr.write('VSET 0')
        instr.write('ISET 0')
        set_rate.write(0)
        pump_on.write(True)
        set_rate.stop()
        pump_on.stop()
        controller.set_sp_loop1(0)

def read_devices(device_list, instr):
    with nidaqmx.Task(new_task_name="Resistivity") as task:
        task.ai_channels.add_ai_voltage_chan(device_list["Water Meter"], max_val=10.0, min_val=0.0)
        data_r = Decimal(value=(float(task.read()) * 2)).quantize(Decimal("0.00"))
        window.resist_val.setText(str(data_r))

    value_v = instr.query('VOUT?')
    data_v = Decimal(value=(re.sub("[^0-9.]", "", value_v))).quantize(Decimal("0.00"))
    window.V_Read.setText(str(data_v) + " V")

    value_a = instr.query('IOUT?')
    data_a = Decimal(value=(re.sub("[^0-9.]", "", value_a))).quantize(Decimal("0.00"))
    window.I_Read.setText(str(data_a * 1000) + " mA")  

    value_t = controller.get_pv_loop1()
    window.temp_val_1.setText(str(value_t))

    window.Power_Calc.setText(str(round((float(data_v) * float(data_a)), ndigits=4)))

def datalog(V_Text, I_Text, P_Text, R_Text, Flow_Text, T_Text, df=pd.DataFrame()):
    df_export = df
    log_time = time.strftime("%Y-%m-%d %H:%M:%S")
    log_dict = {'Time': log_time, 'System State': window.Running, 'Stack Voltage (V)': V_Text, 'Stack Current (mA)': I_Text, 'Stack Power (W)': P_Text, 'Water Resistivity (MΩ)': R_Text, 'Flow Rate (mL/min)': Flow_Text, 'Temperature (°C)': T_Text}
    log_data = pd.DataFrame(data=log_dict, index=[0])
    log_data.to_csv('elec_data.csv', mode='a', index=False, header=False)
    print(time.strftime('%H:%M:%S') + ': Data logged')


if __name__ == "__main__":

    try:
        s = instr.query("ID?")
        pass
    except ValueError:
        print("No power supply detected.")
        sys.exit()
 
    pump_on = pump_start_stop()
    set_rate = pump_flow()
    pump_on.start()
    set_rate.start()
    
    app = QtWidgets.QApplication(sys.argv)
    window = UI_Setup()
    window.show()

    timer_1 = QtCore.QTimer()
    timer_1.timeout.connect(lambda: read_devices(device_list, instr))
    timer_1.start(500)

    #Set the file name to be saved by the system. Must be changed or previous file will be overwritten if it is in the directory.
    try:
        os.remove('elec_data.csv')
    except OSError:
        pass
    log = pd.DataFrame(columns=['Time', 'System State', 'Stack Voltage (V)', 'Stack Current (mA)', 'Stack Power (W)', 'Water Resistivity (MΩ)', 'Flow Rate (mL/min)', 'Temperature (°C)'])
    log.to_csv('elec_data.csv', mode='x', index=False, header=True)

    timer_2 = QtCore.QTimer()
    timer_2.timeout.connect(lambda: datalog(window.V_Read.text(), window.I_Read.text(), window.Power_Calc.text(), window.resist_val.text(), window.settings['Flow'], window.settings['Temp'], log))
    timer_2.start(300 * 1000)

    sys.exit(app.exec())