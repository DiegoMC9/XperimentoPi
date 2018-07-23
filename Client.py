import socket
import sys


close = False
# create TCP/IP socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect to server_address
server_address = (sys.argv[1], 80)
print('connecting to {} port {}'.format(*server_address))
s.connect(server_address)


try:
    while not close:
    # send data
        msg = input('write your message: ').encode()
        print('sending {}'.format(msg))
        s.sendall(msg)
        if msg.decode() == "exit":
            close = True
            break
        #look for response
        amnt_received = 0
        amnt_expected = len(msg)
        while amnt_received < amnt_expected:
            data = s.recv(16)
            amnt_received += len(data)
        if amnt_received == amnt_expected:
            s.sendall(b'done')
            print('OK')
        else:
            print('Error')

finally:
    print('closing socket')
    s.close()
