#!/usr/bin/python

# running this file to run an automated analysis
# and comparison of the three different solutions


import power_analysis
import sys
import os
from create_topo import *

numOfNodes = 3
widex = 100
widey = 100
duration = 600
plotSpectrum = False
plotSignal = True
for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    inputs = arg.split('=')
    if len(inputs) == 2:
        var = inputs[0]
        value = inputs[1]
        if var == "numOfNodes":
            numOfNodes = int(value)
        elif var == 'widex':
            widex = int(value)
        elif var == 'widey':
            widey = int(value)
        elif var == 'duration':
            duration = int(value)
        elif var == 'plotSpectrum':
            plotSpectrum = (value == 'True')
        elif var == 'plotSignal':
            plotSignal = (value == 'True')


node_list = randomly_create(widex, widey, numOfNodes)
link_list = compute_sens(node_list)
write_to_file(link_list)
sys.stderr.write("\nTopology file created\n")
sys.stderr.write("------------------------------------\n")

os.system("/home/jiliac/Development/WSN_Project/running.py loading=basic duration=" + str(duration) + " numOfNodes=" + str(numOfNodes) + " > report_basic.txt ")

sys.stderr.write("\n------------------------------------\n")
sys.stderr.write("--------- Basic Sim runned ----------\n")
sys.stderr.write("-------------------------------------\n")

nothing = open(os.devnull, 'w')
orig_stdout = sys.stdout
sys.stdout = nothing
normal_cps, err1 = power_analysis.power_analysis(plotSpectrum, plotSignal=False, report="report_basic.txt")
sys.stdout = orig_stdout
sys.stderr.write('\nfirst power analysis done\n')

################################################################

os.system("/home/jiliac/Development/WSN_Project/running.py loading=rep duration=" + str(duration) + " numOfNodes=" + str(numOfNodes) + " > report_rep.txt ")

sys.stderr.write("\n------------------------------------\n")
sys.stderr.write("--------- REP Sim runned ------------\n")
sys.stderr.write("-------------------------------------\n")

rep_csp, err_rep = power_analysis.power_analysis(plotSpectrum, plotSignal, report="report_rep.txt")

##############################################################

os.system("/home/jiliac/Development/WSN_Project/running.py loading=dyn duration=" + str(duration) + " numOfNodes=" + str(numOfNodes) + " > report_dyn.txt ")

sys.stderr.write("\n------------------------------------\n")
sys.stderr.write("------- dynamic REP Sim runned -------\n")
sys.stderr.write("-------------------------------------\n")

dynrep_csp, err_dynrep = power_analysis.power_analysis(plotSpectrum, plotSignal, report="report_dyn.txt")

###############################################################

total_normal_csp = .0
total_rep_csp = .0
total_dynrep_csp = .0
for i in range(numOfNodes):
    total_normal_csp = total_normal_csp + normal_cps[i]
    total_rep_csp = total_rep_csp + rep_csp[i]
    total_dynrep_csp = total_dynrep_csp + dynrep_csp[i]
total_energy_saved_rep = (total_normal_csp - total_rep_csp) / total_normal_csp
total_eneger_saved_dyn = (total_rep_csp - total_dynrep_csp) / total_rep_csp
energy_saved_rep = [.0] * numOfNodes
energy_saved_dyn = [.0] * numOfNodes
for i in range(numOfNodes):
    energy_saved_rep[i] = normal_cps[i] - rep_csp[i]
    energy_saved_dyn[i] = rep_csp[i] - dynrep_csp[i]
print("\n\nenergy saved per node by REP solution: " + str(energy_saved_rep))
print("energy saved per node by dynREP solution (compared to REP sol): " + str(energy_saved_dyn))
print("energy saved by REP solution: " + str(total_energy_saved_rep*100) + '%')
print("energy saved by dynREP solution (compared to dynREP sol): " + str(total_eneger_saved_dyn*100) + '%')

total_err_rep = .0
total_err_dynrep = .0
for i in range(numOfNodes):
    total_err_rep = total_err_rep + err_rep[i]
    total_err_dynrep = total_err_dynrep + err_dynrep[i]
err_excess = (total_err_dynrep - total_err_rep) / total_err_dynrep
print("dynREP solution makes " + str(err_excess*100) + "% more errors than REP solution")
print("HistoDataCsp: total_normal_csp="+str(total_normal_csp)+" total_rep_csp="+str(total_rep_csp)+" total_dynrep_csp="+str(total_dynrep_csp))
print("HistoDataErr: err_rep=" + str(total_err_rep/(numOfNodes-1)) + " err_dynrep=" + str(total_err_dynrep/(numOfNodes-1)))
