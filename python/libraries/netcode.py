##"netcode.py" library ---VERSION 0.46---
## - A extra layer of simplification to the Python socket API. Makes netcode really easy -
##Copyright (C) 2025  Lincoln V.
##
##This program is free software: you can redistribute it and/or modify
##it under the terms of the GNU General Public License as published by
##the Free Software Foundation, either version 3 of the License, or
##(at your option) any later version.
##
##This program is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU General Public License for more details.
##
##You should have received a copy of the GNU General Public License
##along with this program.  If not, see <https://www.gnu.org/licenses/>.

import socket
import time #for getting ping
import math #for some timing math

#a counter for our packets - this number can grow quite large, which is why there is a reset counter constant below it...
packet_count = 0
MAX_PACKET_CT = 65535

#the default timeout value for socket.recv() functions
DEFAULT_TIMEOUT = 5.0 #seconds

#the default timeout used to check whether a socket is empty (see clear_socket() below)
DEFAULT_CLEAR_TIMEOUT = 0.75 #seconds

#the default recovery timeout used to get the last bit of data out of the socket to finish one "packet"
DEFAULT_PACKET_TIMEOUT = 0.05 #seconds

#some premade error messages, as well as some constants to help show which message corresponds to which index in the error msgs list
ERROR_MSGS = [
    "[PACKET LOSS] Failed to retrieve buffersize!",
    "[PACKET LOSS] Failed to retrieve an initial data burst through the socket connection!",
    "[PACKET WARNING] Couldn't evaluate the data string INITIALLY - Retrying...",
    "[PACKET WARNING] Couldn't evaluate the data string - Retrying...",
    "[PACKET LOSS] Lost the packet during final evaluation!",
    "[DISCONNECT] Lost 25 packets in a row, and a client has been disconnected!",
    "[PACKET WARNING] Initial error with buffersize data",
    "[SOCKET CLOSED] The socket has been formally closed and no more packets can be exchanged."
    ]
BUFFERSIZE_FAIL = 0 #failed to retrieve buffersize
INITIAL_DATA_BURST = 1 #failed to retrieve the initial burst of data through the socket
INITIAL_EVAL = 2 #this is the first time we try to evaluate a data string. Sometimes works, sometimes doesn't.
EVAL = 3 #>1 time that we try to evaluate a data string. Most packets which enter this phase of recovery come out unscathed.
LOST_EVAL = 4 #>1 time we try to evaluate a data string, and fails.
CONNECTION_LOST = 5 #when we lose so many packets that our connection is considered lost
BUFFERSIZE_WARNING = 6 #we don't get any data initially when we use .recv() to grab the buffersize
SOCK_CLOSE = 7 #if our socket has been formally closed

# - This function acts as a data compressor to reduce netcode transmissions -
#   It removes all the spaces between elements in a "stringifyed" list while keeping spaces in strings
def compress_data(data):
    try: #It is impossible to evaluate a string. This catches data inputs such as strings and directly returns them instead of throwing an error.
        eval(data)
    except: #the data is unevaluateable?
        return data
    if(str(type(eval(data))) == "<class 'list'>"): #if our data is a single element and not a list, there's nothing we can do to compress it.
        quote_depth = 0
        quote_types = [0, 0] #Format: ["#, '#]
        decrement = 0
        for char in range(0,len(data)):
            if(data[char - decrement] == " " and quote_depth == 0): #we found a space which is NOT part of a quote? DELETE IT!
                data = data[0:char - decrement] + data[char - decrement + 1:len(data)]
                #print("removed data @ index " + str(char - decrement) + ". New remainder: " + str(data)) #useful debug info
                decrement += 1
            elif(data[char - decrement] == '"' and quote_types[1] == 0): #we found a quote? We need to find out whether it ENDS or begins a string.
                if(quote_types[0] % 2 == 1): #this will END a string.
                    quote_depth -= 1
                    quote_types[0] -= 1
                else: #it began a string =(
                    quote_depth += 1
                    quote_types[0] += 1
            elif(data[char - decrement] == "'" and quote_types[0] == 0): #we found a quote? We need to find out whether it ENDS or begins a string.
                if(quote_types[1] % 2 == 1): #this will END a string.
                    quote_depth -= 1
                    quote_types[1] -= 1
                else: #it began a string =(
                    quote_depth += 1
                    quote_types[1] += 1
    return data

### - Quick compress_data() test -
##test_samples = [
##    9,
##    True,
##    "string",
##    [0, 1, 2, 3],
##    ["true", "false", "how much data does compress_data() save?", (2, 2)],
##    [True, False, (True, 9)]
##    ]
##compressed = []
##savings = 0
##sample_ct = 1
##for x in test_samples:
##    # - Compress the data -
##    compressed.append(compress_data(str(x)))
##    # - Find the lengths of the original and compressed data, and print out the differences -
##    lengths = [len(str(x)), len(compressed[len(compressed) - 1])]
##    print("Original Length: " + str(lengths[0]) + " - Compressed Length: " + str(lengths[1]))
##    print("\tOriginal Data: " + str(x) + "\n\tCompressed Data: " + str(compressed[len(compressed) - 1]))
##    # - Calculate the average data savings this algorithm provides and print it out -
##    savings += lengths[0] / lengths[1] - 1
##    sample_ct += 1
##savings /= sample_ct
##print("Average savings: " + str(round(savings * 100,3)) + "% data saved.")

# - This function acts as a basic data verification system -
# - Use: give a format list, the function returns whether the data matches your format.
# - How to make a format list: If this was an acceptable data packet: [2, "a", ["abc", 5.07]]
# - Then this would be your format: ["<class 'int'>", "<class 'str'>", ["<class 'str'>", "<class 'float'>"]]
def data_verify(data, verify): #verify is your format list.
    verified = True
    if(str(type(data)) == "<class 'list'>" and str(type(verify)) == "<class 'list'>"): #if the input is a list AND our verify data is a list, the function recursively checks each index. If not...see the else statement...
        if(len(data) != len(verify)): #Is there a disparity between the AMOUNT of data sent and the amount of data expected? This is an immediate red flag that we're not getting good data.
            #print("[NETCODE.py] Length disparity on verify: " + str(len(data)) + " vs expected " + str(len(verify))) #debug
            return False #were OUTTA here
        for x in range(0, len(data)): #data MUST be a list.
            try: #this should work UNLESS we get an IndexError: If an IndexError occurs, that is an immediate red flag that the data we got is NOT what we were looking for.
                verified = data_verify(data[x], verify[x])
            except IndexError:
                verified = False
            if(verified == False): #our test failed at some point??
                break
    elif(verify == "..."): #this is a unpredictable piece of data??
        return True #this counts then.
    else: #we have a single object?
        if(str(type(data)) == verify): #this is a recursive function, so this will work...
            return True
        else:
            #print("[NETCODE.py] Type disparity on verify: " + str(type(data)) + " vs expected " + str(verify) + " with data " + str(data)) #debug
            return False
    return verified

### - Quick function test -
##data = [2, ["abc", 5.74738048109]]
##verify = ["<class 'int'>", ["<class 'str'>", "<class 'float'>"]]
##print(data_verify(data, verify))

#configures a socket so that it works with this netcode library's send/recieve commands - also resets the timeout value to DEFAULT_TIMEOUT
def configure_socket(a_socket, time_override=DEFAULT_TIMEOUT):
    a_socket.setblocking(True)
    a_socket.settimeout(time_override)

def justify(string,size): #a function which right justifies a string
    if(size - len(list(string)) > 0):
        tmpstr = " " * (size - len(list(string)))
        string = tmpstr + string
    return string

def socket_recv(Cs,buffersize): #recieves data, and catches errors.
    errors = None
    data = None
    try:
        data = Cs.recv(buffersize)
    except socket.error: #the socket is broken?
        errors = "disconnect"
    except Exception as e: #a timeout or something else happened?
        print(e)
        errors = "timeout"
    if(not data): #we got NOTHING?
        errors = "disconnect" #we lost connection.
    return data, errors

def send_data(Cs,buffersize,data): #sends some data and checks if the data made it through the wires
    data = compress_data(data) #compress the data to reduce netcode transmissions
    datalen = justify(str(len(list(str(data)))),buffersize)
    data = str(data)
    bytes_ct = 0 #how many characters we have sent
    total_data = datalen + data #the total data string we need to send
    if(Cs._closed): #has the socket been closed?
        return False
    try:
        while (bytes_ct < len(str(total_data)) and Cs.fileno() != -1): #send our our data, making sure that all bytes of it are sent successfully
            bytes_ct += Cs.send(bytes(total_data[bytes_ct:],'utf-8'))
    except Exception as e: #this exception occurs when the socket dies, or if we simply can't send the data for some reason (connection refused?)
        print(e)
        return False #our connection is dead
    return True #our socket is still fine

def recieve_data(Cs,buffersize): #tries to recieve some data without checking its validity
    #   --- Basic setup with some preset variables ---
    global packet_count #a variable which keeps track of how many packets we've recieved.
    global PACKET_TIME #constant which is how long packets should be waited for
    errors = [] #a list of errors - we can append strings to it, which we can then log once the function is completed.
    ping_start = time.time() #set a starting ping time
    data = "" #we set a default value to data, just so we don't get any exceptions from the variable not existing.
    connected = True #are we still connected to the socket properly?
    old_timeout = eval(str(Cs.gettimeout())) #make sure we remember what our initial timeout value was... I use the eval(str()) argument because this otherwise gives me a pointer rather than a float...
    #   --- Handling packet numbering ---
    packet_count += 1
    if(packet_count > MAX_PACKET_CT):
        packet_count = 0
    #   --- get our data's buffersize ---
    Nbuffersize = "" #empty value for our buffersize
    Nbuffersize_data_pack = socket_recv(Cs,buffersize)
    if(Nbuffersize_data_pack[1] == "disconnect"): #we lost da connection
        connected = False
    elif(Nbuffersize_data_pack[1] == 'timeout'):
        errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[BUFFERSIZE_WARNING])
    else:
        Nbuffersize = Nbuffersize_data_pack[0].decode('utf-8')
    while len(list(Nbuffersize)) < buffersize and not Cs._closed: #If Nbuffersize isn't a length of buffersize yet, we need to try recieve a bit more...
        if(Cs._closed): #has the socket been closed?
            connected = False
            errors.append(ERROR_MSGS[SOCK_CLOSED])
            data = None
            break
        data_pack = socket_recv(Cs,buffersize - len(list(Nbuffersize)))
        if(data_pack[1] == "disconnect"): #we got socket.error?
            connected = False #connection lost then...
            break
        elif(data_pack[1] == "timeout"): #we just timed out???
            data = None
            errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[BUFFERSIZE_FAIL])
            break
        else:
            Nbuffersize += data_pack[0].decode('utf-8')
    try:
        Nbuffersize = int(Nbuffersize)
    except:
        errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[BUFFERSIZE_FAIL])
        data = None
    #   --- now we try to grab an initial burst of data ---
    if(data != None and not Cs._closed):
        data_pack = socket_recv(Cs,Nbuffersize)
        if(data_pack[1] == 'disconnect'): #connection lost?
            connected = False
        elif(data_pack[1] == 'timeout'):
            errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[INITIAL_DATA_BURST])
        else:
            data = data_pack[0].decode('utf-8')
    #   --- Now we try to evaluate our data, and hope it just works the first time ---
    initial_success = True
    if(data != None and not Cs._closed):
        try:
            data = eval(data)
        except: #it didn't work? Well then we set this flag so that we know we need to try something else before we count the data as lost...
            errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[INITIAL_EVAL])
            initial_success = False
        #   --- IF we can't evaluate the data string as-is, we try to see if there is ANYTHING left in the socket buffer ---
        if(initial_success == False and not Cs._closed):
            Cs.settimeout(DEFAULT_PACKET_TIMEOUT)
            fail_ct = 0
            while len(list(data)) < Nbuffersize and not Cs._closed: #grab some data if we can
                data_pack = socket_recv(Cs,Nbuffersize - len(list(data)))
                if(data_pack[1] == 'timeout'): #if we got a timeout error, we ran out of data to retrieve...packet LOST
                    errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[LOST_EVAL])
                    fail_ct += 1
                elif(data_pack[1] == 'disconnect'): #well if this happens, we're really out of luck.
                    connected = False
                    fail_ct += 1
                else: #nothing went wrong yet???
                    data += data_pack[0].decode('utf-8')
                try: #try to evaluate the data string again after recieving more tidbits of it
                    data = eval(data) #IF we can evaluate the data, then we break this loop.
                    break
                except: #else, we repeat this loop, trying to grab more data from the buffer cache, and hoping that it completes this data string...
                    errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[EVAL])
                if(fail_ct > 5):
                    data = None
                    break
    # - Clear out the socket if we can't get our data -
    if(data == None):
        connected = clear_socket(Cs)
    #   --- calculate our ping ---
    ping = int(1000.0 * (time.time() - ping_start))
    #   --- Check if the socket has been formally closed ---
    if(Cs._closed):
        errors.append(ERROR_MSGS[SOCK_CLOSE])
        connected = False
    else: #restore our old timeout value
        Cs.settimeout(old_timeout)
    # - Delay till our timeout is hit if we didn't get data (to allow more to buffer in + resync clients/servers) -
    if(data == None):
        if(DEFAULT_TIMEOUT - (time.time() - ping_start) > 0):
            time.sleep(DEFAULT_TIMEOUT - (time.time() - ping_start))
    return [data, ping, errors, connected] #return the data this function gathered

# - Clears out all data within a socket connection -
def clear_socket(Cs):
    old_timeout = eval(str(Cs.gettimeout())) #this gives me a pointer rather than a float...so I need to change that with the eval(str()) argument.
    Cs.settimeout(DEFAULT_CLEAR_TIMEOUT)
    clearing = True
    clear_counter = 0 #this gets incremented each time we get no data from the socket. If we get 2 no-data recv() commands, then we consider the socket cleared.
    while clearing:
        data_pack = socket_recv(Cs, 50) #50 characters at a time?
        data = data_pack[0]
        errors = data_pack[1]
        if(data == None): #we got no data? Increment our clear counter...
            clear_counter += 1
        else: #we got data, socket's still not empty...
            clear_counter = 0
        if(clear_counter > 5): #we're clear?
            clearing = False
        if(errors == "disconnect" or Cs._closed): #we lost connection?
            Cs.settimeout(old_timeout)
            return False #we're disconnected...=(
    Cs.settimeout(old_timeout)
    return True #we're still connected...

# - This class is essentially a replacement for a socket.Socket() object, but data can only be sent between different objects in a local program.
#   Its practical purpose is to allow netcode.py-based online game code to be easily repurposed to help quickly design an offline counterpart -
class DummySocket():
    def __init__(self):
        global DEFAULT_TIMEOUT
        self.linked_socket = None #this will change to a pointer to another socket when you use the connect() function to link this DummySocket() to another one.
        self.sent_data = bytearray() #this holds all data (in binary) which the OTHER DummySocket() needs to still receive but hasn't yet.
        self._closed = False #this flag tells us whether the socket still exists. It does!!
        self.timeout = DEFAULT_TIMEOUT
        self.RETRY_TIME = 0.025

    # - This function links this DummySocket() with another DummySocket() so that they can send data between themselves -
    def connect(self, socket):
        self.linked_socket = socket

    # - This function unlinks this DummySocket() from another DummySocket(). Do not call this function unless this DummySocket() is already linked to another one -
    def disconnect(self):
        self.linked_socket.linked_socket = None #disconnect the socket we're connected to from us (now the other socket can't read data from US)
        self.linked_socket = None #disconnect ourselves from the other socket (now we can't read data from the other socket)

    # - This tries to receive data from the DummySocket() which this socket is connected to -
    def recv(self, buffersize):
        received_data = bytearray()
        if(self.linked_socket != None): #IF we're connected...THEN I guess we'll try receiving data?
            recv_time = time.time()
            for x in range(0,buffersize):
                if(len(self.linked_socket.sent_data) > 0): #if there's data and we need it, we'll TAKE it!
                        received_data.append( self.linked_socket.sent_data.pop(0) )
                else: #if we couldn't get the data, we'll wait a small fraction of a second and then try several more times.
                    #       If that doesn't work, we're going to exit the function and return what we have.
                    while (time.time() - recv_time < self.timeout):
                        time.sleep(self.RETRY_TIME) #there's no point in trying again and again without waiting for data to arrive...
                        if(len(self.linked_socket.sent_data) > 0): #if there's data and we need it, we'll TAKE it!
                            received_data.append( self.linked_socket.sent_data.pop(0) )
                            break
                if(time.time() - recv_time > self.timeout): #make sure we don't spend more time in this function than self.timeout allows.
                    break
        return received_data

    # - This sends data to the DummySocket() which this socket is connected to -
    def send(self, data): #NOTE: data is expected to be a bytes-like object which can be iterated through.
        for x in range(0,len(data)):
            self.sent_data.append(data[x])
        return len(data)

    # - In an offline scenario, this function just needs to return something ELSE than -1 -
    def fileno(self):
        return 1

    # - Set the socket so it will wait a certain amount of time for data -
    def settimeout(self, time):
        self.timeout = time

    # - Retrieve this socket's data wait timeout value -
    def gettimeout(self):
        return self.timeout

    # - Set the socket so it will wait until it gets data -
    def setblocking(self, boolean):
        self.timeout = 9999 #set the value very large

    # - In an offline scenario, this function does not need to do anything since it is purely ping related -
    def close(self):
        pass

### - Quick DummySocket() test -
##sa = DummySocket()
##sb = DummySocket()
##
##sa.connect(sb)
##sb.connect(sa)
##
##sa.send("encoded data".encode('utf-8'))
##sb.send("sb encoded data".encode('utf-8'))
##
##print(sa.recv(7).decode('utf-8'))
##print(sb.recv(7).decode('utf-8'))
