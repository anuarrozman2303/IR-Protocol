dev_id = 'ir_panasonic_ac'         
dev_name = 'IR PANASONIC AC'         
dev_long = 'IR PANASONIC AC' 
dev_desc = 'IR PANASONIC Protocol' 

addrcount = 27

header_addresses = [1, 2, 3, 4, 9, 10, 11, 12]
state_address = [14]
temperature_address = [15]
fan_address = [17]
specialmode_addresses = [22]
chsum_address = [8, 27]

#lc, zero, one, stop, frame frequency(timing)
lc =  0.00515       # 5.15ms
zero = 0.00080      # 0.80ms
one = 0.001763      # 1.763ms
stop = 0.000502     # 0.50ms
frame = 0.01040     # 10.4ms
