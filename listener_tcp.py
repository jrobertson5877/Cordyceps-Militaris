# Main imports
import uuid
import socket
import sys
import os
import signal
import threading
import queue
import time

from handler import Handler

class Listener_TCP(threading.Thread):
    def __init__(self, lhost, lport, agentList, loggers):
        threading.Thread.__init__(self)
        self.lhost = lhost
        self.lport = lport
        self.agentList = agentList
        self.loggers = loggers

        self.max_connections = 1000

    def run(self):

        # Initial socket setup
        try:
            print(f"[* Listener-Msg] Initializing TCP socket on tcp://{self.lhost}:{self.lport}")
            self.loggers[0].q_log('serv','info','[* Listener-Msg] Initializing TCP socket on tcp://'+str(self.lhost)+':'+str(self.lport))

            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_address = (self.lhost, self.lport)

            print(f"[* Listener-Msg] Binding tcp://{self.lhost}:{self.lport} to socket")
            self.loggers[0].q_log('serv','info','[* Listener-Msg] Binding tcp://'+str(self.lhost)+':'+str(self.lport)+' to socket')
            server.bind(server_address)

            print(f"[* Listener-Msg] Listening for {self.max_connections} connections")
            self.loggers[0].q_log('serv','info','[* Listener-Msg] Listening for '+str(self.max_connections)+' connections')            
            server.listen(self.max_connections)

        except Exception as ex:
            print("[* Listener-Msg] Fatal error with socket initialization")
            self.loggers[0].q_log('serv','critical','[* Listener-Msg] Fatal error with socket initialization')
            print(f"[* Listener-Msg] Error: {ex}")
            self.loggers[0].q_log('serv','critical','[* Listener-Msg] Error: '+str(ex))
            os._exit(0)

        print(f"[* Listener-Msg] TCP listener initialized on tcp://{self.lhost}:{str(self.lport)}")
        self.loggers[0].q_log('serv','info','[* Listener-Msg] TCP listener successfully initialized on tcp://'+str(self.lhost)+':'+str(self.lport))            

        self.loggers[0].q_log('serv','info','[* Listener-Msg] Initializing TCP connection record')            
        connRecord = 0                                         # Records Connection ID

        while True:

            (client, client_address) = server.accept()

            print(f"\n[* Listener-Msg] Connection received from {str(client_address[0])}\n")
            self.loggers[0].q_log('serv','info','[* Listener-Msg] Connection received from '+str(client_address[0]))            
            self.loggers[0].q_log('serv','info','[* Listener-Msg] Creating a new Handler thread for '+str(client_address[0]))            
            newConn = Handler(str(uuid.uuid4()), self.loggers, "TCP", client_address, client)
            newConn.start()

            self.agentList.append(newConn)
            connRecord += 1