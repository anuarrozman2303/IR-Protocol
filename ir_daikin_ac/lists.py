dev_id = 'ir_daikin_ac'         
dev_name = 'IR Daikin AC'         
dev_long = 'IR Daikin AC' 
dev_desc = 'IR Daikin AC Protocol' 

addrcount = 35

header_addresses = [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20]
session_addresses = [13, 14, 15, 16]
state_address = [22]
temperature_address = [23]
fan_address = [25]
chsum_address = [8, 16, 35]

#lc, zero, one, stop, frame frequency(timing)
lc =  0.00515       # 5.15ms
zero = 0.00080      # 0.80ms
one = 0.001763      # 1.763ms
stop = 0.000502     # 0.50ms
frame = 0.036032    # 36.032ms
