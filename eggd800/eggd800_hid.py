class EggD800HID(object):
    '''ABC for EGG-D800 HID elements.'''
    def __init__(self):
        self.report_num = None
        self.packed_fmt = None

    @property    
    def output_report(self):
        pass
    
    def get_input_report(self):
        '''Get an input report from the HID handle.'''
        return self.h.get_input_report(self.report_num, self.packed_size)
        
    def set_output_report(self):
        '''Apply current attribute settings to HID handle.'''
        self.h.set_output_report(self.output_report)
