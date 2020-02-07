import os
import re
import pandas as pd
import json
import networkx as nx
import math
import numpy as np

def containsCourseCodes(st):
    codes = re.findall(r'[A-Z]{2,4}\s\d{3}', st)
    return [c.replace('\xa0', ' ') for c in codes]


def sort_courses_by_prereqs(courses, prereqs):
    while True:
        changes_made = False

        for x in range(0, len(courses)):
            if courses[x][0] == "(":
                continue

            if (courses[x] not in prereqs) or (len(prereqs[courses[x]]) == 0):
                continue

            if not set(prereqs[courses[x]]).isdisjoint(courses[x:]): # prereqs for course exist later in the list
                c = courses.pop(x)
                largest_index = x
                for pr in prereqs[c]:
                    if (pr in prereqs) and (c in prereqs[pr]): # sometimes there are circular dependencies, so ignore them
                        continue

                    if pr in courses:
                        i = courses.index(pr)
                        if i > largest_index:
                            largest_index = i

                if largest_index > x:
                    changes_made = True
                    courses.insert((largest_index + 1), c)
                else:
                    courses.insert(x, c)

        if not changes_made:
            break

    return courses


# class for edges
class edge:
    def __init__(self, source, target, label):
        self.source = source
        self.target = target
        self.label = label


# class for nodes
class node:
    def __init__(self, name):
        self.name = name


# class for majors/lines
class major:
    def __init__(self, name, courses):
        self.name = name
        self.courses = courses


# create graph
G = nx.Graph()

# load in prereqs csv from https://github.com/illinois/prerequisites-dataset (so we only do this once)
prereqs = dict()
prereq_table = pd.read_csv("uiuc-prerequisites.csv", header = 0)
for x in range(0, len(prereq_table.index)):
    prereqs[prereq_table.loc[x, 'Course']] = []
    for y in range(0, int(prereq_table.loc[x, 'PrerequisiteNumber'])):
        prereqs[prereq_table.loc[x, 'Course']].append(prereq_table.loc[x, str(y)])

# read in files from /majors folder
for entry in os.scandir("majors"):
    if entry.path.endswith(".txt"):
        major_title = entry.path[7:-4]
        lines = open(entry.path, "r").readlines()

        # create a list of courses that does not include elective categories
        courses = []
        parentheses = 0
        for line in lines:
            if parentheses == 0:
                if line[0] == '"' or line[0] == "“":
                    courses.append(line[1:-3])
                elif (line[0] == "(") and (line[len(line) - 3] == ")"):
                    codes = containsCourseCodes(line)
                    if ("MATH 221" in codes) and ("MATH 220" in codes) and (len(codes) == 2): # yeah if its just those two idc
                        courses.append("MATH 221")
                    else:
                        courses.append(line[0:-2])
                else:
                    if "(" in line:
                        parentheses += line.count("(")

                    if ")" in line:
                        parentheses -= line.count(")")
            else:
                if "(" in line:
                    parentheses += line.count("(")

                if ")" in line:
                    parentheses -= line.count(")")

        # sort courses by prereq
        courses = sort_courses_by_prereqs(courses, prereqs)

        # add each course to nodes (if dne), and add an edge to the next node
        for x in range(0, len(courses)):
            if not G.has_node(courses[x]): # add node to graph
                G.add_node(courses[x])

            if x != (len(courses) - 1): # add edges to graph
                G.add_edge(courses[x], courses[x + 1], major=major_title)

# graph drawing part:

def calc_smallest_angle(x1, y1, x2, y2, x3, y3): # find the smallest angle between meeting line segments where x2, y2 is the vertex
    a = np.array([x1, y1])
    b = np.array([x2, y2])
    c = np.array([x3, y3])

    ab = b - a
    bc = c - b
    cb = b - c
    ba = a - b

    angle1 = math.acos(np.dot(ab, bc) / (np.linalg.norm(ab) * np.linalg.norm(bc)))
    angle2 = math.acos(np.dot(cb, ba) / (np.linalg.norm(cb) * np.linalg.norm(ba)))

    if angle1 < angle2:
        return angle1

    return angle2


def angularResolution_calc(n, G):
    # neighbors of input node
    E = G.neighbors(n)

    sum = 0
    for i in range(0, len(E) - 1): # between i and i + 1
        angle = calc_smallest_angle(G[E[i]]['x'], G[E[i]]['y'], G[n]['x'], G[n]['y'], G[E[i + 1]]['x'], G[E[i + 1]]['y'])
        sum += abs(((2*math.pi) / len(E)) - angle)
    return sum


def angularResolution(G): # The angles of incident edges at each station should be maximized
    sum = 0
    for n in G.nodes():
        sum += angularResolution_calc(n, G)
    return sum


def edgeLength(G): # The edge lengths across the whole map should be approximately equal
    l = 4 # prefered multiple (grid spacing g assumed as 1)

    sum = 0
    for e in G.edges():
        length = math.hypot(G[e[0]]['x'] - G[e[1]]['x'], G[e[0]]['y'] - G[e[1]]['y'])
        sum += abs((length / l) - 1)
    return sum


def balancedEdgeLength(G): # penalizing stations with degree two that have incident edges with unbalanced lengths
    sum = 0
    for n in G.nodes():
        E = G.edges(n)
        if len(E) == 2:
            e_one = math.hypot(G[E[0][0]]['x'] - G[E[0][1]]['x'], G[E[0][0]]['y'] - G[E[0][1]]['y'])
            e_two = math.hypot(G[E[1][0]]['x'] - G[E[1][1]]['x'], G[E[1][0]]['y'] - G[E[1][1]]['y'])
            sum += abs(e_one - e_two)
    return sum


def lineStraightness(G): # Edges that form part of a line should, where possible, be collinear either side of each station that the line passes through
    sum = 0
    for n in G.nodes():
        # get edges of n
        inner_sum = 0
        E = G.edges(n, data=True)

        if (len(E) > 1):
            # get majors that go through n
            lines = [i[2]['major'] for i in E]

            # iterate through majors, isolate the edges of that major, and perform the angle calculation
            for l in lines:
                e12 = [i for i in E if i[2]['major'] == l]
                if len(e12 == 2): # not a terminating node for this line
                    n1 = ""
                    n2 = ""

                    if e12[0][0] != n:
                        n1 = e12[0][0]
                    else:
                        n1 = e12[0][1]

                    if e12[1][0] != n:
                        n2 = e12[1][0]
                    else:
                        n2 = e12[1][1]

                    inner_sum += calc_smallest_angle(G[n1]['x'], G[n1]['y'], G[n]['x'], G[n]['y'], G[n2]['x'], G[n2]['y'])

        sum += inner_sum

    return sum


def octilinearity(G): # Each edge should be drawn horizontally, vertically, or diagonally at 45 degree
    sum = 0
    for e in G.edges():
        sum += math.abs(math.sin(4 * math.atan(math.abs(G[e[0]]['y'] - G[e[1]]['y']) / math.abs(G[e[0]]['x'] - G[e[1]]['x']))))
    return sum


def calcStationCriteria(G): # The criteria evaluate to a lower value when improved
    return 30000*angularResolution(G) + 50*edgeLength(G) + 45*balancedEdgeLength(G) + 220*lineStraightness(G) + 9250*octilinearity(G)


def findLowestStationCriteria(G):
    return 0


def clusterOverlengthEdges(G):
    return []


def clusterBends(G): # return a list
    return []


def clusterPartitions(G): # return a list
    return []


def moveStation(v):
    pass


def moveCluster(p):
    pass


# create an initial layout -- assign x and y coordinates to graph on a grid
height = 4
width = math.floor(G.number_of_nodes() / (height - 1))
pos = {}
x = 1
y = 1
for n in G.nodes():
    pos[n] = (x, y)

    if (x == width):
        x = 1
        y += 1
    else:
        x += 1

# calculate initial layout fitness
mto = calcStationCriteria(G)

running = True

while running:
    # stations
    for v in G.nodes():
        mno = calcStationCriteria(G)
        mn = findLowestStationCriteria(G)
        if mn < mno:
            moveStation(v)

    # station clusters
    P = clusterOverlengthEdges(G) + clusterBends(G) + clusterPartitions(G)
    for p in P
        mno = calcStationCriteria(G)
        mn = findLowestStationCriteria(G)
        if mn < mno:
            moveCluster(p)

    # TODO: labels

    mt = calcStationCriteria(V)
    if not mt < mto:
        running = False
    else:
        mto = mt

# create json file
# final = json.dumps({'nodes': [n.__dict__ for n in list(nodes.values())], 'edges': [e.__dict__ for e in edges], 'majors': [m.__dict__ for m in majors]})
# open("graph.json", "a").write(final)
