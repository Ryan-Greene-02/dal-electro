# dal-electro
An all-encompassing control suite for a custom electrolyzer. Created by Ryan Greene, 2025.
# Specifications
This system is designed to function through the use of specific analytical instruments and power supplies, but can be modified to operate with multiple different instruments. The base specifications are:\
* An HP6032A System Power Supply, currently sold by Keysight\
* A NE-9000 Peristalic Pump from New Era Pump Systems Inc.\
* A 750II Resistive Water Meter from the Myron L. Company\
* A CN-402-1114455-C4 PID Control Unit from DwyerOmega\
Other instruments can be substituted by altering the ports and encoding software located in the repository.
# Python Libraries used
* PyQt6
* decimal
* nidaqmx
* time
* pyvisa
* re
* sys
* os
* pandas
* minimalmodbus