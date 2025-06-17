import minimalmodbus

class OmegaPID(minimalmodbus.Instrument):
    '''
    Instrument class for Omega CN402-1114455-C4 PID controller

    Args:
        * portname (str): address
        * slaveaddress (int): instrument address in range of 1 to 247
    '''

    def __init__(self, portname, slaveaddress):
        minimalmodbus.Instrument.__init__(self, portname, slaveaddress)

    def status_check(self):
        self.read_register(0, 1)
        return print("Heat control connected")

    def get_pv_loop1(self):
        return self.read_register(1000, 1)
    
    def set_sp_loop1(self, value):
        self.write_register(1200, value, 1)
        return self.read_register(1200, 1)