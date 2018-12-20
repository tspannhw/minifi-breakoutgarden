import socket
TCP_IP = 'hw13125.local'
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = '{"systemtime": "12/19/2018 20:33:42", "BH1745_green": "20.0", "ltr559_prox": "0002", "end": "1545269622.36", "uuid": "20181220013342_3b954379-b308-42d3-98b4-ef3d86f215d7", "lsm303d_accelerometer": "+00.05g : -01.01g : +00.03g", "imgnamep": "images/bog_image_p_20181220013342_3b954379-b308-42d3-98b4-ef3d86f215d7.jpg", "cputemp": 45.0, "BH1745_blue": "21.6", "te": "9.77740502357", "bme680_tempc": "27.75", "imgname": "images/bog_image_20181220013342_3b954379-b308-42d3-98b4-ef3d86f215d7.jpg", "bme680_tempf": "81.95", "ltr559_lux": "000.00", "memory": 11.9, "VL53L1X_distance_in_mm": 0, "bme680_humidity": "25.874", "host": "vid5", "diskusage": "8781.0", "ipaddress": "192.168.1.167", "bme680_pressure": "1016.94", "BH1745_clear": "90.0", "BH1745_red": "0.0", "lsm303d_magnetometer": "-00.21 : +00.33 : +00.14", "starttime": "12/19/2018 20:33:32"}\n'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.sendall(MESSAGE)
s.close()
