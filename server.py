#!/usr/bin/python3

# Main imports
import socket
import sys
import os
import signal
import threading
import queue
import time

# Project imports
from interpreter import Interpreter
from listener_tcp import Listener_TCP
from logger import Logger
from listener_http import Listener_HTTP
# from listener_dns import Listener_DNS

agentList = []                  # Stores client_address[] info (IP, Port): IP is stored in string format, port is not

                                # [Handler-ID]-[client_address]-[ IP ]
                                #            |                L-[Port]
                                #            L-[CMD_Queue]

interpreters = []               # Literally only here to access outside of MAIN

loggers = []                    # List of Loggers from easier access across modules

listeners = []                  # Handles all listening threads (TCP, HTTP, DNS, etc...)
                                # Ensuring that information can be passed between them and allowing for easier management

# -------------------------------------------------------------------------------------------

# TODO
#      - Test Kill function


# Catch CTRL-C
def catchSIGINT(signum, frame):

    print(f"\n[* Server-Msg] Please exit gracefully!")
    print(f"[* Server-Msg] Either use the EXIT command or EXIT whatever mode you are interacting in.")
    print(f"[* Server-Msg] Ungraceful exit behavior causes shells and connections to break...")

    try:
        signal.signal(signal.SIGINT, original_sigint)
        if(interpreters):
            interpreters[0].exit()
            os._exit(0)
        else:
            os._exit(0)
    
    except KeyboardInterrupt:
        if(interpreters):
            interpreters[0].exit()
            os._exit(0)
        else:
            os._exit(0)
        print(f"[* Server-Msg] HEATHEN!!!\n")

    signal.signal(signal.SIGINT, catchSIGINT)
        
def main():

    # if (len(sys.argv) < 3):
    #     print(f"[* Server-Msg] Usage:\n  [+] python3 {sys.argv[0]} <LHOST> <LPORT>\n  [+] Eg.: python3 {sys.argv[0]} 0.0.0.0 1337\n")
    # else:

    os.system("clear")
    print("\n<=[Starting the C2]=>")

    try:
        print("[* Server-Msg] Initializing Logger module...")
        LoggerThread = Logger()                                 # Handles interface, queue is for commands
        LoggerThread.start()
        loggers.append(LoggerThread)
        print("[* Server-Msg] Logger initialization complete...")
        loggers[0].q_log('serv','info','[* Server-Msg] Logger initialization complete')                  # Working
    except Exception as ex:
        print(f"[* Server-Msg] Unable to start logging service. Exiting...")
        loggers[0].q_log('serv','critical','[* Server-Msg] Unable to start logging service. Exiting...')                  # << WIP
        print(f"[* Server-Msg] Error: {ex}")
        loggers[0].q_log('serv','critical','[* Server-Msg] Error: ' + str(ex))

        os._exit(0)
    
    loggers[0].q_log('serv','info','[* Server-Msg] Initializing server...')                  # << WIP
    time.sleep(1)

    print('''
/\______________________________________________________________________/\\
|                                                                        |
|       CORDYCEPS MILITARIS                                              |
|                             /\       .    /\\                           |
|                            / /       \\\\  / /      /\                   |
|                        /\  \ \    /\  \\\\/ /      / /                   |
|                       / /   \ \.==\ \==\ (==/\=./ /   /\               |
|               /\      \ \.==*\ \###\ \##\ \#\ \/ /*=. \ \              | 
|               \ \  /\  \//###/ /###{_/@@@\_}#\  /###\\\\ \ \  /\         |
|                \ \/ /  //###{_/#@@######@@@@@/ /#####\\\\ \ \/ /         |
|                 \  /  //#####@___________##@/ /@######\\\\/ / /          | 
|                  \ \  (|####@[  __       ]##\ \@@######/  _/           | 
|                  / /  (|##__@[ /  \ |\/| ]@##\ \_@####/ /)             |
|   /\   /\        \ \  (|#/  }[ |    |  | ]@@##\  }###/ /|)             | 
|   ||   ||         \ \_(|/  /@[ \__/ |  | ]@###@\_}##{ /#|)             | 
|  (XX) (XX)         \______/#@[___________]####@@@###{/##//             |
|   \ \  \ \      _______(\########@@__/ /####@@@@#######//              |
|    \ \--\ \----/        (\########{___/####@@@@#######//               |
|     \ (..\....           (\.=._.=._.=-=..__.=..=._.=.//_               |
|     (___________________________________________________)              |
|                                                                        |
|                                                                        |
|========================================================================|
|   Produced by:                                                         |
|                                                                        |      
|          Josh Robertson    Andrew Linscott     Dalton Brown            |
| ______________________________________________________________________ |
\/                                                                      \/
    ''') 

    print("\n\n\n\t[Welcome to the Cordyceps-Militaris command and control framework]\n")

#### ADDRESS ENTRY ####

    loggers[0].q_log('serv','info','[* Server-Msg] Address entry initiated')

    address_entry_success = False
    while not address_entry_success:
        try:
            print("[* Server-Msg] Please enter the address you would like to start the listeners on, e.g. 0.0.0.0")
            address_entry = input('[* Address-Entry]% ')
        # Input error
        except Exception as ex:
            print(f"[* Server-Msg] Unable to process address entered...")
            loggers[0].q_log('serv','error','[* Server-Msg] Unable to process address entered. Retrying...')
            print(f"[* Server-Msg] Error: {ex}")
            loggers[0].q_log('serv','error','[* Server-Msg] Error: ' + str(ex))
            continue

        # No input
        if not address_entry:
            print("[* Server-Msg] No input received. Please retry...\n")
            loggers[0].q_log('serv','warning','[* Server-Msg] No input received. Retrying...')

        else:
            # Test if valid address
            try:
                socket.inet_aton(address_entry)
            # Invalid format
            except socket.error:
                print("[* Server-Msg] Invalid address received. Please retry...\n")
                loggers[0].q_log('serv','warning','[* Server-Msg] Invalid address "'+str(address_entry)+'" received. Retrying...')
                continue
            
            # Confirm
            print(f"[* Server-Msg] Is the address entered correct [Y/n]: {address_entry}")
            try:
                confirm_entry = input('[* Confirm]% ')
            # Input error
            except Exception as ex:
                print(f"[* Server-Msg] Unable to process confirmation..")
                loggers[0].q_log('serv','error','[* Server-Msg] Unable to process confirmation...')
                print(f"[* Server-Msg] Error: {ex}")
                loggers[0].q_log('serv','error',('[* Server-Msg] Error: ' + str(ex)))

                continue
            else:
                # Yes
                if confirm_entry.casefold().strip(" ") == 'y' or confirm_entry.casefold().strip(" ") == '':
                    lhost = address_entry
                    print(f"[* Server-Msg] Address set to {address_entry}...")
                    loggers[0].q_log('serv','info',('[* Server-Msg] Server address set to: ' + str(address_entry)))
                    address_entry_success = True
                # Anything else
                else:
                    print(f"[* Server-Msg] Unable to confirm address...")
                    loggers[0].q_log('serv','info','[* Server-Msg] Unable to confirm address')



#### LISTENER SELECTION ####

    print("[* Server-Msg] Select which type of listeners you would like to use. You may choose more than one.")
    loggers[0].q_log('serv','info','[* Server-Msg] Listener prompt initiated')

    listener_entry_success = False

    while not listener_entry_success:
        print('''
[* Server-Msg] Please type them as a space-seperated list, ie. '0 1 2', without apostrophes.
[* Server-Msg] Or, type 'quit' to exit.\n
\t\t[0] Standard TCP
\t\t[1] HTTP
\t\t[2] DNS\n
        ''')

        try:
            listener_entry_list = input('[* Select Listeners]% ').split()
        except Exception as ex:
            print(f"[* Server-Msg] Fatal error with input. Exiting...")
            loggers[0].q_log('serv','critical','[* Server-Msg] Fatal error with input. Exiting...')
            print(f"[* Server-Msg] Error: {ex}")
            loggers[0].q_log('serv','critical',('[* Server-Msg] Error: ' + str(ex)))
            os._exit(0)
        else:

            if(not listener_entry_list):
                print("[* Server-Msg] No input received. Please retry...\n")
                loggers[0].q_log('serv','error','No input received. Please retry...')
                listener_entry_success = False
                continue

            if("quit" in listener_entry_list):
                print("[* Server-Msg] Exiting...")
                os._exit(0)

            try:
                # TCP
                if("0" in listener_entry_list):

                    # Port entry and verification
                    port_entry_success = False
                    while not port_entry_success:
                        try:
                            print("[* Server-Msg] Please enter the port you would like to start the TCP listeners on, e.g. 31337")
                            port_entry = int(input('[* Port-Entry]% '))
                        # Input error
                        except Exception as ex:
                            print(f"[* Server-Msg] Unable to process port entry")
                            loggers[0].q_log('serv','warning','[* Server-Msg] Unable to process port entry')
                            print(f"[* Server-Msg] Error: {ex}")
                            loggers[0].q_log('serv','warning',('[* Server-Msg] Error: ' + str(ex)))
                            continue

                        # No input
                        if not port_entry:
                            print("[* Server-Msg] No input received. Please retry...\n")
                            loggers[0].q_log('serv','warning',('[* Server-Msg] No port number entered'))
                        else:
                            # Confirm
                            print(f"[* Server-Msg] Is the port entered correct [Y/n]: {port_entry}")
                            try:
                                confirm_entry = input('[* Confirm]% ')
                            # Input error
                            except Exception as ex:
                                print(f"[* Server-Msg] Unable to process confirmation. Retry...")
                                loggers[0].q_log('serv','warning','[* Server-Msg] Unable to process confirmation')
                                print(f"[* Server-Msg] Error: {ex}")
                                loggers[0].q_log('serv','warning',('[* Server-Msg] Error: ' + str(ex)))
                                continue
                            else:
                                # Yes?
                                if confirm_entry.casefold().strip(" ") == 'y' or confirm_entry.casefold().strip(" ") == '':
                                    lport = port_entry
                                    print(f"[* Server-Msg] Port set to {port_entry}...")
                                    loggers[0].q_log('serv','info','[* Server-Msg] TCP Listener port set to: '+str(port_entry))
                                    port_entry_success = True
                                # Anything else?
                                else: 
                                    continue
                    
                    # Initiate TCP Listener thread
                    print("[* Server-Msg] Creating TCP Listener thread...")
                    try:
                        loggers[0].q_log('serv','info','[* Server-Msg] Creating TCP Listener Thread with address '+str(lhost)+' and port '+str(lport))
                        TCP_Thread = Listener_TCP(lhost, lport, agentList, loggers)
                        TCP_Thread.start()
                        listeners.append(TCP_Thread)
                        listener_entry_success = True
                    except Exception as ex:
                        print("[* Server-Msg] Fatal error with TCP listener creation. Exiting...")
                        loggers[0].q_log('serv','critical','[* Server-Msg] Fatal error with TCP listener creation')
                        print(f"[* Server-Msg] Error: {ex}")
                        loggers[0].q_log('serv','critical','[* Server-Msg] Error: ' + str(ex))
                        os._exit(0)


                ## FUTURE IMPLEMENTATION - socket for thread init
                if("1" in listener_entry_list):
                    try:
                        HTTP_Thread = Listener_HTTP(agentList, loggers)
                        HTTP_Thread.start()
                        listeners.append(HTTP_Thread)
                        listener_entry_success = True
                    except Exception as ex:
                        print("[* Server-Msg] Fatal error with listener selection and initialization. Exiting...")
                        print(f"[* Server-Msg] Error: {ex}")
                        os._exit(0)

                if("2" in listener_entry_list):
                    # DNS_Thread = Listener_DNS(lhost, lport, agentList, loggers)
                    # DNS_Thread.start()
                    # listeners.append(DNS_Thread)
                    print("[* Server-Msg] Function yet to be included")
                    # entry_success = False

            except Exception as ex:
                print("[* Server-Msg] Fatal error with listener selection and thread creation. Exiting...")
                loggers[0].q_log('serv','critical','[* Server-Msg] Fatal error with listener selection and thread creation')
                print(f"[* Server-Msg] Error: {ex}")
                loggers[0].q_log('serv','critical','[* Server-Msg] Error: ' + str(ex))
                os._exit(0)

    time.sleep(2)
    print("[* Server-Msg] Initializing Interpreter session...")

    try:
        InterpreterThread = Interpreter(agentList, listeners, loggers)          # Handles interface, queue is for commands
        InterpreterThread.start()
        interpreters.append(InterpreterThread)
        loggers[0].q_log('serv','info','[* Server-Msg] Interpreter thread initialization complete')


    except Exception as ex:
        print(f"[* Server-Msg] Failed to initialize Interpreter thread")
        loggers[0].q_log('serv','critical','[* Server-Msg] Failed to initialize Interpreter thread')
        print(f"[* Server-Msg] Error: {ex}")
        loggers[0].q_log('serv','critical',f'[* Server-Msg] Error: ' + str(ex))
        os._exit(0)

if __name__ == '__main__':
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, catchSIGINT)
    main()
