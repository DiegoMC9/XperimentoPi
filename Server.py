import RPi.GPIO as GPIO
from time import sleep
from random import choice
import socket
import sys
from multiprocessing import Queue, Process
# first lets create the messages queue
q = Queue()
IP = "192.168.1.127"

# GPIO to LCD mapping
LCD_RS = 7 # Pi pin 26
LCD_E = 8 # Pi pin 24
LCD_D4 = 25 # Pi pin 22
LCD_D5 = 24 # Pi pin 18
LCD_D6 = 23 # Pi pin 16
LCD_D7 = 18 # Pi pin 12

# Device constants
LCD_CHR = True # Character mode
LCD_CMD = False # Command mode
LCD_CHARS = 16 # Characters per line (16 max)
LCD_LINE_1 = 0x80 # LCD memory location 1st line
LCD_LINE_2 = 0xC0 # LCD memory location 2nd line

E_DELAY = 0.0005

# Define main program code
def display(q):
    RIGHT = True
    LEFT = False

    # Initialize display
    lcd_init()
    # Loop - send text and sleep 3 seconds between texts
    # Change text to anything you wish, but must be 16 characters or less
    while True:
        lcd_text(IP, LCD_LINE_2)
        if not q.empty():
            roll(q.get(), choice([RIGHT,LEFT]))
        else:
            lcd_text("No messages left", LCD_LINE_1)

# roll text (string, boolean) True->Right-left, False-> Left-Right
def roll(msg, right):
    disp = " "*LCD_CHARS + msg + " "*LCD_CHARS
    if right:
        for i in range(len(disp)-16):
            lcd_text(disp[len(disp)-i-LCD_CHARS:len(disp)-i], LCD_LINE_1)
            sleep(0.25)

    else:
        for i in range(len(disp)-16):
            lcd_text(disp[i:i+LCD_CHARS], LCD_LINE_1)
            sleep(0.25)

# Initialize and clear display
def lcd_init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM) # Use BCM GPIO numbers
    GPIO.setup(LCD_E, GPIO.OUT) # Set GPIO's to output mode
    GPIO.setup(LCD_RS, GPIO.OUT)
    GPIO.setup(LCD_D4, GPIO.OUT)
    GPIO.setup(LCD_D5, GPIO.OUT)
    GPIO.setup(LCD_D6, GPIO.OUT)
    GPIO.setup(LCD_D7, GPIO.OUT)
    # Initialise display
    lcd_write(0x33,LCD_CMD) # 110011 Initialise
    lcd_write(0x32,LCD_CMD) # 110010 Initialise
    lcd_write(0x06,LCD_CMD) # 000110 Cursor move direction
    lcd_write(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
    lcd_write(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
    lcd_write(0x01,LCD_CMD) # 000001 Clear display
    sleep(E_DELAY)

def lcd_write(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True  for character
    # False for command
    GPIO.output(LCD_RS, mode) # RS

    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits&0x10==0x10:
        GPIO.output(LCD_D4, True)
    if bits&0x20==0x20:
        GPIO.output(LCD_D5, True)
    if bits&0x40==0x40:
        GPIO.output(LCD_D6, True)
    if bits&0x80==0x80:
        GPIO.output(LCD_D7, True)

        # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits&0x01==0x01:
        GPIO.output(LCD_D4, True)
    if bits&0x02==0x02:
        GPIO.output(LCD_D5, True)
    if bits&0x04==0x04:
        GPIO.output(LCD_D6, True)
    if bits&0x08==0x08:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

def lcd_toggle_enable():
    # Toggle enable
    sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    sleep(E_DELAY)
    GPIO.output(LCD_E, False)
    sleep(E_DELAY)

def lcd_text(message,line):
    # Send text to display
    if len(message)<16:
        message = message.ljust(LCD_CHARS," ")

    lcd_write(line, LCD_CMD)
    print(message)
    for i in range(LCD_CHARS):
        lcd_write(ord(message[i]),LCD_CHR)

def wake_server(q):
    #run = True
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Create TCP/IP socket
    # Bind the socket to the port
    server_address = ('', 80)
    print('starting up on {} port {}'.format(*server_address))
    sock.bind(server_address)
    # Listen for incoming connections
    sock.listen(1)
    while True:
        msg = ""
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
                    q.put(msg)
                    print('adding {} to queue'.format(msg))
                    msg = ""
                elif data == b'exit':
                    print('Disconnected: ', client_address)
                    break
                elif data:
                    msg += data.decode()
                    print('sending data back to the client')
                    connection.sendall(data)
                else:
                    print('Disconnected: ', client_address)
                    break

        finally:
            # Clean up the connection
            #run = False
            connection.close()

if __name__ == '__main__':
    #Begin program
    try:
        server = Process(name='server', target=wake_server, args = (q, ))
        LCD = Process(name='LCD', target=display, args = (q, ))
        server.daemon = True
        LCD.daemon = True
        server.start()
        LCD.start()
        server.join()
        #LCD.terminate()
        LCD.join()
    except KeyboardInterrupt:
        pass
    finally:
        lcd_write(0x01, LCD_CMD)
        lcd_text("Goodbye",LCD_LINE_1)
        lcd_text(" ",LCD_LINE_2)
        GPIO.cleanup()
