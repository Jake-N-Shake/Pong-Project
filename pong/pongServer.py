# Contributing Authors: Jacob Dohoney-Pilling, Brett Hoskins	                               
# Email Addresses: jrdo235@uky.edu, xbho222@uky.edu                                      
# Date: 11/21/23                                            
# Purpose: Code for pong game server side that connects and interacts with the client.
# Misc: 
# ======================================================================================================================= #

import socket
import threading
import sys
import time
import json

# Authors: Jacob Dohoney-Pilling, Brett Hoskins             
# Purpose: Manages the connection with the client side
# Pre: Client must send instructions to the server
# Post: Server gives the requested information to the client
def updateServer(client_soc:socket.socket) -> None:

        # Takes message from client and decodes it
        response = client_soc.recv(1024).decode()
        requestClient = json.loads(response)
        # Makes sure that only the gameState data is accessable
        semaphore.acquire()
        # Use data from client to update gameState's dictionary
        gameState[client_soc] = requestClient
        semaphore.release()

# Authors: Jacob Dohoney-Pilling, Brett Hoskins                
# Purpose: Manages the process of the server updating the client
# Pre: Client must request to synchronize the game
# Post: Server updates the client and resolves issues with sychronization
def updateServerResponse() -> None:

    # Makes sure that only the gameState data is accessable
    semaphore2.acquire()

    # Checks to see if the first client's gameState dicitionary is behind the second's, and updates the first's if it is
    if gameState[socketsClient[0]]["sync"] < gameState[socketsClient[1]]["sync"]:
        gameState[socketsClient[0]] = { 
                        "playerPaddle": gameState[socketsClient[0]]["playerPaddle"],
                        "opponentPaddle": gameState[socketsClient[1]]["playerPaddle"],
                        "ball": gameState[socketsClient[1]]["ball"], 
                        "lScore": gameState[socketsClient[1]]["lScore"],
                        "rScore": gameState[socketsClient[1]]["rScore"],
                        "sync": gameState[socketsClient[1]]["sync"] }

    else:
        gameState[socketsClient[1]] = { 
                        "playerPaddle": gameState[socketsClient[1]]["playerPaddle"],
                        "opponentPaddle": gameState[socketsClient[0]]["playerPaddle"],
                        "ball": gameState[socketsClient[0]]["ball"],
                        "lScore": gameState[socketsClient[0]]["lScore"],
                        "rScore": gameState[socketsClient[0]]["rScore"],
                        "sync": gameState[socketsClient[0]]["sync"] }

        # Makes sure that the relation between "player" and "opponent" paddle is flipped depending on client perspective
        gameState[socketsClient[0]]["opponentPaddle"] = gameState[socketsClient[1]]["playerPaddle"]

    semaphore2.release()

# Server specificatiions
serverIP = 'localhost'
serverPort = 5050

socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socketServer.bind((serverIP, serverPort))
socketServer.listen(5)

# Semaphores are used so that there is access control to the gameState dictionary, and so the clients can avoid race conditions 
semaphore = threading.Semaphore(1)
semaphore2 = threading.Semaphore(1)
gameSpecs = list()
socketsClient = list()

# Authors: Jacob Dohoney-Pilling, Brett Hoskins             
# Purpose: Sets up connections with the clients 
while len(socketsClient) < 2:

    gameMetricsClient = {"widthScreen": 800,
                         "heightScreen": 600,
                         "paddlePlayer": ("left" if len(socketsClient) == 0 else "right")}
    gameSpecs.append(gameMetricsClient)
    
    # Accepts the connection to the client 
    clientSocket, clientIP = socketServer.accept()
    # Adds the newly connected client to the list
    socketsClient.append(clientSocket)

# Game specifications are sent to both the clients in order to start the game
socketsClient[0].send(json.dumps(gameSpecs[0]).encode())
socketsClient[1].send(json.dumps(gameSpecs[1]).encode())

# Sets up the gameState dictionary for both of the clients
gameState = {value: {"playerPaddle": [0, 0, ""], "opponentPaddle": [0, 0, ""], "ball": [0, 0], "lScore": 0, "rScore": 0, "sync": 0} for value in socketsClient}

connected = True

# Authors: Jacob Dohoney-Pilling, Brett Hoskins             
# Purpose: Manages the clients via threads that while loop gameState until the match finishes
while connected:

    # Semaphores are used so that there is access control to the gameState dictionary, and so the clients can avoid race conditions 
    threads = []
    for sock in socketsClient:
        client = threading.Thread(target=updateServer, args=(sock,))
        threads.append(client)

    threads[0].start(), threads[1].start()
    threads[0].join(), threads[1].join()

    # Server compares and updates both clients' gameState dictionaries
    updateServerResponse()

    # Updated gameStates are sent to both clients
    socketsClient[0].send(json.dumps(gameState[socketsClient[0]]).encode()) 
    socketsClient[1].send(json.dumps(gameState[socketsClient[1]]).encode())

# Close the client and server sockets
for sock in socketsClient:
    sock.close()

socketServer.close()
