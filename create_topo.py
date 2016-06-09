#!/usr/bin/python

# to create random node topology
# could also read node placement from a file
# no need to directly use this file, integrated in analysis

from collections import namedtuple
from math import sqrt
from random import uniform


##############################
#### In case of input file for placement
##############################

Node = namedtuple("Node", "node_nb x y")
def read(to_read):
    lines = open(to_read, "r")
    node_list = []
    for line in lines:
        values = line[:-1].split()
        node_nb = int(values[0])
        x = float(values[1])
        y = float(values[2])
        node = Node(node_nb, x, y)
        node_list.append(node)
    return node_list
#node_list = read("placement")
#numOfNodes = len(node_list)
#print('number of node: ' + str(numOfNodes))

##############################
###### random placement of nodes
##############################

def randomly_create(widex, widey, numOfNodes):
    node_list = []
    node_counter = 0
    for node_nb in range(numOfNodes):
        x = uniform(0, widex)
        y = uniform(0, widey)
        node = Node(node_counter, x, y)
        node_counter = node_counter + 1
        node_list.append(node)
    return node_list
node_list = randomly_create(100, 100, 3)

##############################
##### Compute sensitivity
##############################

def distance(x1, y1, x2, y2):
    return sqrt((x1-x2)**2 + (y1-y2)**2)
Link = namedtuple("Link", "node1 node2 sensitivity")

def compute_sens(node_list):
    numOfNodes = len(node_list)
    link_list = []
    
    for node_nb1 in range(0, numOfNodes-1):
        for node_nb2 in range(node_nb1+1, numOfNodes):
            node1 = node_list[node_nb1]
            node2 = node_list[node_nb2]
            dist = distance(node1.x, node1.y, node2.x, node2.y)
            if dist < 100:
                dist = '-' + str(dist)
                link1 = Link(str(node_nb1+1), str(node_nb2+1), dist)
                link2 = Link(str(node_nb2+1), str(node_nb1+1), dist)
                link_list.append(link1)
                link_list.append(link2)
    return link_list


def write_to_file(link_list):
    ##############################
    ##### creating topo.txt file
    ##############################
    
    topo = open("topo.txt", "w")
    to_write = ""
    for link in link_list:
        string = link.node1 + " " + link.node2 + " " + link.sensitivity + "\n"
        to_write = to_write + string
    topo.write(to_write)
