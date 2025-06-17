def convert(value, src_unit, dest_unit):
    MAP = {
            ('ul',     'ml'):     lambda x: x*1e-3,
            ('ml',     'ul'):     lambda x: x*1e3,
            ('ul/min', 'ml/min'): lambda x: x*1e-3,
            ('ul/min', 'ul/h'):   lambda x: x*60.0,
            ('ul/min', 'ml/h'):   lambda x: x*60e-3,
            ('ml/min', 'ul/min'): lambda x: x*1e3,
            ('ml/min', 'ul/h'):   lambda x: x*60e3,
            ('ml/min', 'ml/h'):   lambda x: x*60,
            ('ul/h',   'ml/h'):   lambda x: x*1e-3,
            }
    if src_unit == dest_unit:
        return value
    return MAP[src_unit, dest_unit](value)


#####################################################################
# Custom-defined pump error messages
#####################################################################


class NewEraPumpError(Exception):
    """
    General pump error
    """

    def __init__(self, code, mesg=None):
        self.code = code
        self.mesg = mesg

    def __str__(self):
        result = '%s\n\n%s' % (self._todo, self._mesg[self.code])
        if self.mesg is not None:
            result += ' ' + self.mesg
        return result


class NewEraPumpCommError(NewEraPumpError):
    """
    Handles error messages resulting from problems with communication via the
    pump's serial port

    See section 12.3 Command Errors and Alarms of pump manual
    """

    _mesg = {
            # Actual codes returned by the pump
            ''      : 'Command is not recognized',
            'NA'    : 'Command is not currently applicable',
            'OOR'   : 'Command data is out of range',
            'COM'   : 'Invalid communications packet recieved',
            'IGN'   : 'Command ignored due to new phase start',
            # Custom codes
            'NR'    : 'No response from pump',
            'SER'   : 'Unable to open serial port',
            'UNK'   : 'Unknown error',
            }

    _todo = 'Unable to connect to pump. Ensure the correct address, port, and baudrates were used. If not, please ' \
            'ensure that no other programs that utilize the pump are running and try power-cycling the entire system.'


class NewEraPumpHardwareError(NewEraPumpError):

    """
    Handles errors specific to the pump hardware and firmware.

    Ses section 12.2.4 RS-232 Protocol: Basic and Safe Mode Common Syntax of pump manual

    """
    # these mesg are the <alarm type> for the RS-232 protocol
    _mesg = {
            'R'     : 'Pump was reset due to power interrupt',
            'S'     : 'Pump motor is stalled',
            'T'     : 'Safe mode communication time out',
            'E'     : 'Pumping program error',
            'O'     : 'Pumping program phase out of range',
            }

    _todo = 'Pump has reported an error.  Please check to ensure pump ' + \
            'motor is not over-extended and power-cycle the pump.'


class NewEraPumpUnitError(Exception):
    """
    Occurs when the pump returns a value in an unexpected unit

    """

    def __init__(self, expected, actual, cmd):
        self.expected = expected
        self.actual = actual
        self.cmd = cmd

    def __str__(self):
        mesg = '%s: Expected units in %s, receved %s'
        return mesg % (self.cmd, self.expected, self.actual)

