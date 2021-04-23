from dnstun import dns_answer_create, dns_header_create, udp_header_create, ip_header_create
from socket import socket, inet_aton, AF_INET, SOCK_RAW, SOCK_DGRAM, IPPROTO_RAW, IPPROTO_IP, IP_HDRINCL


sock=socket(AF_INET, SOCK_DGRAM)
bufferSize = 255                               #max message size

serverip="127.0.0.1"  #just hard coded for now
server_port=53        #just hard coded for now
server_domain="red.team".strip('.') #remove '.' from server domain
server_domain_len=len(server_domain) #get length of server domain

def receive_query(packet :bytearray, client_ip, client_port):
    message = str
    
    id = int.from_bytes(packet[0:2], "big")          #get transaction id
    i=0
    message=''
    while True:    #extract the message #need to filter port inputs
        domain_len = int.from_bytes(packet[12+i:13+i], "big")    #get length of subdomain section
        if domain_len==0: break                                  #if it is the null terminator exit loop
        message += packet[13+i:13+i+domain_len].decode('idna')   #decode the encoded message
        i += domain_len+1                                        #increment the index to next subdomain
    message=message[:-server_domain_len+1]                       #remove server domain from message
    
    #send response
    packet=dns_answer_create(packet[12:13+i])                    #reteive queried domain
    packet=dns_header_create(id,'1', '0011')+packet              #create dns header; qr:1=ans, rcode:3=nx domain
    sock.sendto(packet, (client_ip, client_port))                #send a reply
    return message

def listen():
    sock.bind((serverip, server_port))
    while(True):
        bytes=sock.recvfrom(bufferSize)
        print(receive_query(bytes[0], bytes[1][0], bytes[1][1]))
listen()