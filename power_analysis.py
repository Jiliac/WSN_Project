#!/usr/bin/python 

# perform an analysis based on the output of the running script
# by default this output file is supposed to be named report.txt
# I have not made anything to run this file directly
# Used by the analysis script

from collections import namedtuple
import numpy as np
from math import sin
from scipy.fftpack import fft, ifft
import matplotlib.pyplot as plt

def power_analysis(plotSpectrum=False, plotSignal=True, report = "report.txt", printREPTime=False):
    lines = open(report, 'r')
    
    #####################
    # Parsing Info
    #####################
    
    def to_time(time_string):
        strings = time_string.split(':')
        time = int(strings[0]) * 3600 + int(strings[1]) * 60 + float(strings[2])
        return time
    
    started = False
    numOfNodes = 0
    node = []
    string = []
    times = []
    max_out = 0
    for line in lines:
        s = line.split()
        if (len(s) > 0):
            if started == False:
                if(s[0] == "START"):
                    started = True
                    numOfNodes = int(s[5])
            elif s[0] == "END":
                break
            else:
                node.append(int(s[2][1:2])-1)
                string.append(s[3:])
                times.append(to_time(s[0]))
                max_out = max_out+1
    ending_time = int(times[-1])+1
    print("ending time: " + str(ending_time) + ' s')
    
    #print(node)
    #print(string)
    
    ###################
    # REP Inclusion
    ###################
    # Give REPresentative node values to ASSOCiated nodes
    if printREPTime:
        print("\n --------------------------------------------------")
        print(" ------------------ REP Parsing -------------------")
        print(" --------------------------------------------------\n")
    representing = namedtuple("representing", "start_time end_time assoc_node rep_node")
    reps = [[] for y in range(numOfNodes)]
    tmp = []
    print('number of nodes: ' + str(numOfNodes))
    for output_nb in range(max_out):
        node_nb = node[output_nb]
        time = times[output_nb]
        output = string[output_nb]
        if output[0] == "Sleeping":
            rep_node = int(output[-1])-1
            rep_time = representing(time, -1, node_nb, rep_node)
            tmp.append(rep_time)
        elif output[0] == "Waking" and len(output) == 7:
            rep_node = int(output[-1])-1
            for rep_time in tmp:
                if rep_time.end_time == -1 and rep_time.assoc_node == node_nb and rep_time.rep_node == rep_node:
                    new_rep_time = representing(rep_time.start_time, time, rep_time.assoc_node, rep_time.rep_node)
                    tmp.remove(rep_time)
                    reps[rep_node].append(new_rep_time)
                    break

    time_in_rep_mode = [.0] * numOfNodes
    for node_nb in range(1, numOfNodes):
        if printREPTime:
            print('Node ' + str(node_nb) + ' is ASSOCiated with:')
        for rep_time in reps[node_nb]:
            rep_duration = rep_time.end_time - rep_time.start_time
            time_in_rep_mode[node_nb] = time_in_rep_mode[node_nb] + rep_duration
            if printREPTime:
                print(rep_time)
        if printREPTime:
            print('\n------------ ANOTHER NODE NEXT ------------\n')
    
    def is_rep(node_nb, time):
        assoc_list = []
        for rep_time in reps[node_nb]:
            if time > rep_time.start_time and rep_time.end_time > time:
                assoc_list.append(rep_time.assoc_node)
        return assoc_list

    
    ###################
    # Signal Reconstruction
    ###################
    DEFAULT_INTERVAL = 256.0      # same as in Sensing.h - in millisecond
    sensing_value = namedtuple("sensing_value", "time value")
    sampled_values = [[] for y in range(numOfNodes)]
    
    def plot(sampled, filtered):
        N = (ending_time-1)*1000/DEFAULT_INTERVAL
        abscisse = np.linspace(0, ending_time*len(sampled)/N, len(sampled))
        plt.plot(abscisse, sampled)
        plt.plot(abscisse, filtered)
        plt.grid()
        plt.legend(['sampled', 'filtered'])
        plt.show()
    
    # getting sensed values
    for output_nb in range(max_out):
        node_nb = node[output_nb]
        time = times[output_nb]
        output = string[output_nb]
        if(output[0] == "Reading"):
            # normal sensing
            sensed = sensing_value(time, float(output[4]))
            sampled_values[node_nb].append(sensed)
            # taking in account REPresentatives
            for assoc_node in is_rep(node_nb, time):
                rep_sensed = sensing_value(time, float(output[4]))
                sampled_values[assoc_node].append(rep_sensed)
    
    
    # get signal using fourier transform
    # start from 1 because 0 is base station, not sensing
    filtered_values = [[] for y in range(numOfNodes)]
    for node_nb in range(1, numOfNodes):
        x = []
        for point in sampled_values[node_nb]:
            x = x + [point.value]
        print('node : ' + str(node_nb+1) + ' has sensed ' + str(len(x)) + " values")
        if len(x) != 0:
            y = np.array(x)
    
            # plotting spectrum
            if plotSpectrum:
                plt.plot(np.linspace(0, len(y), len(y)), np.log(np.abs(fft(y))))
                plt.grid()
                plt.show()
    
            # we just keep 2% slowest and fatest frequencies
            filtered_limit = len(y)/50
            fourrier = fft(y)
            fourrier[filtered_limit:-filtered_limit] = 0
            signal = ifft(fourrier, len(y))
            signal = np.abs(signal)
            #for value in signal:
            for i in range(len(signal)):
                value = signal[i]
                filtered_values[node_nb].append(sensing_value(sampled_values[node_nb][i].time, value))
            if plotSignal:
                plot(y, signal)
    
    
    ###################
    # Sampling Performance
    ###################
    
    def original_signal(node_nb, time):
    #formula from tos/system/SineSensorC.nc
        signal_value = (sin((time/5) + (node_nb+1)) + 1) * 32768.0
        return signal_value
    
    # This block was just if the original_signal() function was working correctly
    #errors_test = [.0]*numOfNodes
    #for sensed in sampled_values:
    #    print("sensed value : " + str(sensed.value) + " - orginal: " + str(original_signal(sensed.node_nb, sensed.time)) + ' - time: ' + str(sensed.time) + ' - node_nb: ' + str(sensed.node_nb))
    #    error = np.abs(sensed.value - original_signal(sensed.node_nb, sensed.time))
    #    errors_test[sensed.node_nb] = errors_test[sensed.node_nb] + error
    #for node_nb in range(1, numOfNodes):
    #    errors_test[node_nb] = errors_test[node_nb] / len(filtered_values[node_nb])
    #print(errors_test)
    
    errors = [.0]*numOfNodes
    for node_nb in range(1, numOfNodes):
        for point in filtered_values[node_nb]:
            #print("sampled value is " + str(point.value) + ", whereas anoligical value is " + str(original_signal(node_nb, point.time)) + ' - time: ' + str(point.time) + ' - node_nb: ' + str(node_nb))
            error = np.abs(point.value - original_signal(node_nb, point.time))
            errors[node_nb] = errors[node_nb] + error
        if len(filtered_values[node_nb]) != 0:
            errors[node_nb] = errors[node_nb] / len(filtered_values[node_nb])
        else:
            print('error, no value sensed by node ' + str(node_nb) + " - error: " + str(errors[node_nb]))
            errors[node_nb] = -1
    print('\naverage error for each node: ' + str(errors))
    print('time spent in rep mode: ' + str(time_in_rep_mode) + "\n")
    
    ###################
    # Analysing power consumption
    ###################
    VOLTAGE = 3
    RADIO_SEND_I = 17.4 * 0.001
    RADIO_RECEIVED_I = 19.7 * 0.001
    DATA_RATE = 250
    CPU_I = 8 * 0.001
    # 3V, 19.7mA, 250kbps
    # value from MICAz mote documentation
    # assuming a 3V battery...
    power_csp = [.0] * numOfNodes
    booted_time = [0] * numOfNodes
    
    def add_consumption(node, cost, packet_size):
        to_add = VOLTAGE * cost * packet_size / DATA_RATE
        power_csp[node_nb] = power_csp[node] + to_add
        
    
    # networking power consumption
    for output_nb in range(max_out):
        node_nb = node[output_nb]
        output = string[output_nb]
        if(output[0] == 'Booted'):
            booted_time[node_nb] = times[output_nb]
            print('node ' + str(node_nb+1) + ' booted at t=' + str(times[output_nb]))
        else:
            packet_size = 0
            try:
                packet_size = int(output[-1])
                packet_size = packet_size + 11 + 7 + 5  # header, metadata, footer sizes
                packet_size = packet_size * 8 * 0.001   # conversion from byte to kbit 
            except ValueError:
                pass
            cost = 0
            if(len(output) > 2 and output[1] == 'Sending' and output[2] == 'around'):
                cost =  RADIO_SEND_I
            elif(len(output) > 1 and output[1] == 'Received' and (output[4] == 'from' or output[4] == 'Signaling')):
                # 'from' option in case of normal DYMO forwarding or reception
                # 'Signaling' one in case of broadcasting reception
                code = RADIO_RECEIVED_I
                if output[4] == 'from':
                    # in this case we also have to take into account the loss of the sender
                    sender_node_nb = int(output[5])-1
                    add_consumption(sender_node_nb, RADIO_SEND_I, packet_size)
            add_consumption(node_nb, cost, packet_size)
    
    # CPU power consumption
    awake_intervals = [[]] * numOfNodes
    node_sleeping = [False] * numOfNodes
    last_awake = [booted_time[node_nb] for node_nb in range(numOfNodes)]
    for output_nb in range(max_out):
        node_nb = node[output_nb]
        if(string[output_nb][0] == 'Sleeping'):
            time = times[output_nb]
            node_sleeping[node_nb] = True
            awake_intervals[node_nb] = awake_intervals[node_nb] + [last_awake[node_nb], time]
        elif(string[output_nb][0] == "Waking" and node_sleeping[node_nb]):
            time = times[output_nb]
            node_sleeping[node_nb] = False
            last_awake[node_nb] = time
    for node_nb in range(numOfNodes):
        if(not node_sleeping[node_nb]):
            awake_intervals[node_nb] = awake_intervals[node_nb] + [last_awake[node_nb], ending_time] 
    for node_nb in range(numOfNodes):
        for i in range(len(awake_intervals[node_nb])/2):
            running_time = awake_intervals[node_nb][2*i+1] - awake_intervals[node_nb][2*i]
            power_csp[node_nb] = power_csp[node_nb] + running_time * VOLTAGE * CPU_I
    
    print("\n------- power consumption of node -------\n")
    print(power_csp)
    return power_csp, errors
