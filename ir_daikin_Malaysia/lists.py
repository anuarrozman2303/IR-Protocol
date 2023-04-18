dev_id = 'ir_daikin_Malaysia'        
dev_name = 'IR Daikin Malaysia AC'          
dev_long = 'IR Daikin Malaysia AC' 
dev_desc = 'IR Daikin Malaysia AC Protocol' 

addrcount = 8

mode = ["HEADER","MODES","TEMP","CHS"," " ]

header_addresses = [1, 2, 3, 4, 9, 10, 11, 12]
state_address = [8]
temperature_address = [7]

#lc, zero, one, stop, frame frequency(timing)
lc =  0.007238       # 5.15ms
zero = 0.00075      # 0.80ms
one = 0.00133      # 1.763ms
stop = 0.025150     # 0.50ms
frame = 0.02    # 36.032ms
