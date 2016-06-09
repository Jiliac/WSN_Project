#!/usr/bin/python

# to create a bar graph from the output of the analysis script
# make f (line 19) points towards the file where you stored your output

import numpy as np
import matplotlib.pyplot as plt

####################################
############ Get Data ##############
####################################

csp_normal = []
csp_rep = []
csp_dynrep = []
err_rep = []
err_dynrep = []

f = open("final_report.txt", "r")
for line in f:
    output = line.split()
    if len(output) > 1:
        if output[0] == "HistoDataCsp:":
            csp = float(output[1].split('=')[1])
            csp_normal = csp_normal + [csp]
            csp = float(output[2].split('=')[1])
            csp_rep = csp_rep + [csp]
            csp = float(output[3].split('=')[1])
            csp_dynrep = csp_dynrep + [csp]
        elif output[0] == "HistoDataErr:":
            err = float(output[1].split('=')[1])
            err_rep = err_rep + [err/32768.0]
            err = float(output[2].split('=')[1])
            err_dynrep = err_dynrep + [err/32768.0]

####################################
######## Plot Consumption ##########
####################################

index = np.arange(len(csp_normal))
bar_width = 0.25
rects1 = plt.bar(index, csp_normal, bar_width,
        color='b', label='Normal Consumption', alpha=0.4)
rects2 = plt.bar(index + bar_width, csp_rep, bar_width,
        color='g', label='REP Consumption', alpha=0.4)
rects3 = plt.bar(index + 2*bar_width, csp_dynrep, bar_width,
        color='r', label='Adaptive REP Consumption', alpha=0.4)
plt.ylabel("Consumption (J)")
plt.title("Consumption of different WSN solutions")
plt.xticks(index + 2*bar_width, ['test'+str(i) for i in range(len(csp_normal))])
plt.legend()

plt.tight_layout()
plt.show()

####################################
############ Plot Error ############
####################################

bar_width = 0.35
rects1 = plt.bar(index, err_rep, bar_width,
        color='g', label='REP Error', alpha=0.4)
rects2 = plt.bar(index + bar_width, err_dynrep, bar_width,
        color='r', label='Adaptive REP Error', alpha=0.4)
plt.ylabel("Error (normalized by signal amplitude)")
plt.title("Error made by different WSN solutions")
plt.xticks(index + bar_width, ['test'+str(i) for i in range(len(csp_normal))])
plt.legend()

plt.tight_layout()
plt.show()
