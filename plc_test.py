# ************************ #
# This code reads input from PLC to perform Point,Position and Sequence    #
# based goal and provide acknlowedgements                                  #
# ************************ #

import pymcprotocol
import time

class plc_test():
    def _init_():
        #connecting to plc 
        pymc3e = pymcprotocol.Type3E()
        pymc3e.connect("192.168.0.39", 8892)

        while (pymc3e._is_connected==True):
            #Keep on sending a pluse signal of 1sec to register X306 to sure plc is always connected
            pymc3e.randomwrite_bitunits(bit_devices=["X306"], values=[1])
            time.sleep(1)
            pymc3e.randomwrite_bitunits(bit_devices=["X306"], values=[0])
            time.sleep(1)
if _name_ == '_main_':
    plc_test()