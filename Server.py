import socket
import sys
import queue
# first lets create the messages queue
q = queue.Queue()
msg = ""

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('', 80)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)

        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(16)
            #print('received {}'.format(data))
            if data == b'done':
                print('received {}'.format(msg))
                q.put(msg)
                msg = ""
            elif data:
                msg += data.decode()
                print('sending data back to the client')
                connection.sendall(data)
            else:
                print('no data from', client_address)
                while not q.empty():
                    print(q.get())
                break
    finally:
        # Clean up the connection
        connection.close()
