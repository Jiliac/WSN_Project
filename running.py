#!/usr/bin/python

# file to run one of the three solution
# can be run without any argument
# used by analysis script, so this file can be use directly, but no need to

import sys
import random
import tqdm
import sys

def run(numOfNodes, duration=200, DYMO_DEBUG=False, topoFile = 'topo.txt', noiseFile = 'noise.txt', loading="rep"):
# simulation duration (sec)

    ########################
    # Define Variable
    ########################
    startTime = 1   # bode boot up (sec)
    t = None
    if loading == "basic":
        sys.path.append('/home/jiliac/Development/WSN_Project/Basic_Sensing')
        import TOSSIM as BASIC
        t = BASIC.Tossim([])
    elif loading == "dyn":
        sys.path.append('/home/jiliac/Development/WSN_Project/dynREP')
        import TOSSIM as DYNREP
        t = DYNREP.Tossim([])
    elif loading == "rep":
        sys.path.append('/home/jiliac/Development/WSN_Project/REP')
        import TOSSIM as REP
        t = REP.Tossim([])
    r = t.radio()
    
    ########################
    # Get topology info
    ########################
    f = open(topoFile, "r")
    lines = f.readlines()
    for line in lines:
        s = line.split()
        if(len(s) > 0):
            print(s[0] + '  ' + s[1] + "  " + s[2])
            r.add(int(s[0]), int(s[1]), float(s[2]))
    
    #######################
    # Get noise
    #######################
    noise = open(noiseFile, "r")
    lines = noise.readlines()
    for line in lines:
        string = line.strip()
        if(string != ""):
            val = int(string)
            for i in range(1, numOfNodes+1):
                t.getNode(i).addNoiseTraceReading(val)
    
    for i in range(1, numOfNodes+1):
        print("Creating noise model for " + str(i))
        t.getNode(i).createNoiseModel()
    
    #######################
    # Debugging out
    #######################
    t.addChannel("Boot", sys.stdout)
    t.addChannel("Sleep", sys.stdout)
    t.addChannel("fwe", sys.stdout)
    t.addChannel("REP", sys.stdout)
    t.addChannel("Report", sys.stdout)
    
    if DYMO_DEBUG:
        t.addChannel("Networking", sys.stdout)
        t.addChannel("AMQueue", sys.stdout)
        t.addChannel("messages", sys.stdout)
        t.addChannel("mhe", sys.stdout)
        t.addChannel("de", sys.stdout)
        t.addChannel("dt", sys.stdout)
    
    ########################
    # Start Simulation
    ########################
    print("\nSTART - nb of nodes: " + str(numOfNodes) + "\n")
    # start running every node at startTime
    DEFAULT_INTERVAL = 256
    for i in range(1, numOfNodes+1):
        m = t.getNode(i)
        rand = random.randint(0, DEFAULT_INTERVAL) * 0.001
        m.bootAtTime(long((startTime + rand) * t.ticksPerSecond()))
    
    time = t.time()
    previous_time = time
    pbar = tqdm.tqdm(total=100)
    while (time + (duration * 10000000000) > t.time()):
        t.runNextEvent()
        new_advance = float(t.time() - previous_time)
        to_update = 100 * new_advance / (duration * 10000000000)
        previous_time = t.time()
        pbar.update(to_update)
    pbar.clear()
    pbar.close()
    
    print("END")

_numOfNodes = 3
_duration = 600
_loading = "rep"
_topoFile = "topo.txt"
for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    inputs = arg.split('=')
    if len(inputs) == 2:
        var = inputs[0]
        value = inputs[1]
        if var == "numOfNodes":
            _numOfNodes = int(value)
        elif var == "duration":
            _duration = int(value)
        elif var == "loading":
            _loading = value
        elif var == "topoFile":
            _topoFile = value
run(numOfNodes=_numOfNodes, duration=_duration, loading=_loading, topoFile=_topoFile)
