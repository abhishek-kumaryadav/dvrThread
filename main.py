import threading
import numpy as np
from queue import Queue
import time
from tabulate import tabulate
import sys
import copy

# Global Dictionary to Map Index -> RouterName
dicti = {}

# main():
#       acceptInput( createDictionary, adjacentRouterTable, routingTables)
#       initialize( single lock + queue per node, barrier to synchronize)
#       launch router threads, wait then join them
def main(fname):
    global dicti  # Using global dictionary
    # Opening and reading file line by line
    f = open(fname, "r")
    lines = f.readlines()
    dict = {}  # Inverse dictionary to Map RouterName -> Index
    routerNum = int(lines.pop(0).strip())  # Getting number of routers
    allTables = (
        np.ones((routerNum, routerNum)) * np.inf
    )  # Creating combined routingTable filled with inf
    adjRouters = [
        list() for f in range(routerNum)
    ]  # Empty adjacentRouter table initialization
    # Populating dictionary and reverseDictionary
    for routerName in enumerate(lines.pop(0).strip().split(" ")):
        dict[routerName[1]] = routerName[0]
    dicti = {v: k for k, v in dict.items()}
    # Populating combined routingTable and adjacentRouters
    for line in lines:
        if line.strip() != "EOF":
            first, second, weight = line.strip().split(" ")
            adjRouters[dict[first]].append(dict[second])
            adjRouters[dict[second]].append(dict[first])
            allTables[dict[first], dict[second]] = weight
            allTables[dict[second], dict[first]] = weight

    # Initializing a queue and lock per node indexed using dictionary
    # Initializing barrier to synchronize all threads
    allQueues = []
    locks = []
    for i in range(0, routerNum):
        allTables[i, i] = 0
        allQueues.append(Queue())
        locks.append(threading.Lock())
    barrier = threading.Barrier(routerNum)

    # print: routers, adjacentRouters, routingTables
    print("Routers:\t{}".format(dicti))
    print("Adjacent routers:\t{}".format(adjRouters))
    print("Routing Tables:\n{}".format(allTables))
    print("Queue, Locks and Barrier Initialized")
    print("INITIALIZATION FINISHED")
    print("\n________________________________________________________\n")

    # Initializing thread for each node
    threads = []
    for i in range(0, routerNum):
        th = threading.Thread(
            target=router,
            args=(i, allTables[i], allQueues, adjRouters[i], locks, barrier),
        )  # threadArguments: ( routerIdIndex, all Queues and Locks and a barrier, routingTable, adjacentRouters for current node, )
        threads.append(th)
        th.start()
    # Waiting for threads to finish then join()
    for t in threads:
        t.join()
    # Closing the file
    f.close()


#
# Router Function: wait -> sendTable -> receiveUpdate -> printData
#
def router(idRouter, rTable, sharedQ, adjRouters, locks, barrier):

    # Using global dictionary to Map Index -> RouterName
    global dicti
    # Initiazing indexed nextHop which will be starting node
    nextHop = list(range(0, len(rTable)))
    # Running Distance Vector Routing 'iterations' times
    iterations = 4
    for i in range(0, iterations):
        # Waiting for 5 secs
        time.sleep(5)

        # Acquiring lock for all adjacent nodes one by one and sending data through respective queue
        # data = (node.routingTable, senderIndex)
        for adj in adjRouters:
            locks[adj].acquire()
            dcopy = copy.deepcopy(rTable)
            sharedQ[adj].put((dcopy, idRouter))
            locks[adj].release()
        # This barrier conommitted and instead locks can be used to retrieve data to maintaining concurrency and data integrity
        # I have used barrier to simplify code execution and understanding
        # barrier.wait()  # Waiting for everyone to send data

        # Retreiving data and calculating new routing Table
        updated = [0] * len(rTable)  # Used to check if node.routingTable gets updated
        for adj in adjRouters:
            newTable, senderId = sharedQ[idRouter].get(True)  # Getting data from queue
            # Calculating new routingTable and updating 'updated'
            costSender = rTable[senderId]
            for j in range(0, len(rTable)):
                #     for j in range(0, len(rTable[0])):
                if not (rTable[j] == np.inf and newTable[j] == np.inf):
                    if rTable[j] > newTable[j] + costSender:
                        rTable[j] = newTable[j] + costSender
                        nextHop[j] = senderId
                        updated[j] = 1
            # newTable.free()

        # Wait for all threads to finish computation
        barrier.wait()

        # Priting this router's info
        nextHopStr = [dicti[v] for v in nextHop]
        rTableStar = []
        for m in range(0, len(rTable)):
            strr = str(rTable[m])
            if updated[m] == 1:
                strr = strr + "*"
            rTableStar.append(strr)
        table = [rTableStar, nextHopStr]
        print(
            "\n---------------{}------ITR:{}-------\n{}".format(
                dicti[idRouter],
                i + 1,
                tabulate(transpose(table), headers=["Cost", "NextHop"]),
            )
        )


# Transposes a List
def transpose(l1):
    l2 = []
    l2 = [[row[i] for row in l1] for i in range(len(l1[0]))]
    return l2


# Run main()
if __name__ == "__main__":

    main(sys.argv[1])