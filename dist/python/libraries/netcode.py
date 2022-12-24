##"netcode.py" library ---VERSION 0.38---
##Copyright (C) 2022  Lincoln V.
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

#a counter for our packets - this number can grow quite large, which is why there is a reset counter constant below it...
packet_count = 0
MAX_PACKET_CT = 65535

#the default timeout value for socket.recv() functions
DEFAULT_TIMEOUT = 5.0 #seconds

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

# - This function acts as a basic data verification system -
# - Use: give a format list, the function returns whether the data matches your format.
# - How to make a format list: If this was an acceptable data packet: [2, "a", ["abc", 5.07]]
# - Then this would be your format: ["<class 'int'>", "<class 'str'>", ["<class 'str'>", "<class 'float'>"]]
def data_verify(data, verify): #verify is your format list.
    verified = True
    if(str(type(data)) == "<class 'list'>" and str(type(verify)) == "<class 'list'>"): #if the input is not a list AND our verify data isn't a list, the function works like this. If not...see the else statement...
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
            return False
    return verified
### - Quick function test -
##data = [2, ["abc", 5.74738048109]]
##verify = ["<class 'int'>", ["<class 'str'>", "<class 'float'>"]]
##
##print(data_verify(data, verify))

#configures a socket so that it works with this netcode library's send/recieve commands - also resets the timeout value to DEFAULT_TIMEOUT
def configure_socket(a_socket):
    a_socket.setblocking(True)
    a_socket.settimeout(DEFAULT_TIMEOUT)

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

def send_data(Cs,buffersize,data): #sends some data without checking if the data made it through the wires
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
    else: #this occurs if data != None
        if(initial_success == False and not Cs._closed):
            Cs.settimeout(0.35)
            while len(list(data)) < Nbuffersize and not Cs._closed: #grab some data if we can
                data_pack = socket_recv(Cs,Nbuffersize - len(list(data)))
                if(data_pack[1] == 'timeout'): #if we got a timeout error, we ran out of data to retrieve...packet LOST
                    errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[LOST_EVAL])
                    break
                elif(data_pack[1] == 'disconnect'): #well if this happens, we're really out of luck.
                    connected = False
                    break
                else: #nothing went wrong yet???
                    data += data_pack[0].decode('utf-8')
                try: #try to evaluate the data string again after recieving more tidbits of it
                    data = eval(data) #IF we can evaluate the data, then we break this loop.
                    break
                except: #else, we repeat this loop, trying to grab more data from the buffer cache, and hoping that it completes this data string...
                    errors.append("(" + justify(str(packet_count),5) + ") " + ERROR_MSGS[EVAL])
    # - Clear out the socket if we can't get our data -
    if(data == None):
        connected = clear_socket(Cs)
    #   --- calculate our ping ---
    ping = int(1000.0 * (time.time() - ping_start))
    #   --- Check if the socket has been formally closed ---
    if(Cs._closed):
        errors.append(ERROR_MSGS[SOCK_CLOSE])
        connected = False
    else:
        configure_socket(Cs)
    return [data, ping, errors, connected] #return the data this function gathered

# - Clears out all data within a socket connection -
def clear_socket(Cs):
    Cs.settimeout(0.75)
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
        if(clear_counter > 1): #we're clear?
            clearing = False
        if(errors == "disconnect" or Cs._closed): #we lost connection?
            return False #we're disconnected...=(
    configure_socket(Cs)
    return True #we're still connected...
            
