OVERVIEW:
This is the implant/agent that is used to receive and execute commands from the command and control server (C2) then send results back to the server. 
The implant uses http over port 5000 to communicate with the server and all messages are in json format.

INSTRUCTIONS:
To set/change the ip address of the C2, edit /win_http_sp0re/win_http_sp0re/main.cpp and change the host variable on line 24 to the desired ip.
You will then need to recompile the whole solution using visual studio. 
Note: 	The boost library will cause the solution to not compile if the language is not set to C++ 17.
	To change this setting in visual studio 19, go to 
	project -> properties -> configuration properties -> general -> C++ language standard 
	and ensure it is set to "ISO C++17 Standard (/std:c++17)"
The executable can be found at /win_http_sp0re/x64/debug/win_http_sp0re.exe
Note:	In the current state of the implant, it requires some supplemental files in the same folder as the executable such as dlls and an ilk.
	This is subject to change.