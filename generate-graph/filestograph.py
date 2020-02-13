import os
import re
import pandas as pd
import json
import networkx as nx
from networkx.readwrite import json_graph
import math
import numpy as np
import itertools

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


def read_in_files(foldr_name, prereqs):
    G = nx.MultiDiGraph()

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

    return G


# graph drawing functions:

def calc_smallest_angle(x1, y1, x2, y2, x3, y3): # find the smallest angle between meeting line segments where x2, y2 is the vertex
    # TODO: check that this is radians
    a = np.array([x1, y1])
    b = np.array([x2, y2])
    c = np.array([x3, y3])

    ab = b - a
    bc = c - b
    cb = b - c
    ba = a - b

    angle1 = np.arccos(np.dot(ab, bc) / (np.linalg.norm(ab) * np.linalg.norm(bc)))
    angle2 = np.arccos(np.dot(cb, ba) / (np.linalg.norm(cb) * np.linalg.norm(ba)))

    if angle1 < angle2:
        return angle1

    return angle2


def line_intersection(x1, y1, x2, y2, x3, y3, x4, y4): # return true if the lines intersect at any point that is not the start, end, or full line
# http://www.cs.swan.ac.uk/~cssimon/line_intersection.html
    if (x1 == x3 and y1 == y3) or (x1 == x4 and y1 == y4) or (x2 == x3 and y2 == y3) or (x2 == x4 and y2 == y4):
        return False # same line / same origin point case

    a_num = ((y3 - y4) * (x1 - x3)) + ((x4 - x3) * (y1 - y3))
    b_num = ((y1 - y2) * (x1 - x3)) + ((x2 - x1) * (y1 - y3))
    denom = ((x4 - x3) * (y1 - y2)) - ((x1 - x2) * (y4 - y3))

    if (denom == 0):
        return False # lines are parallel

    ta = a_num / a_denom
    tb = b_num / b_denom

    if (ta > 1 or ta < 0) or (tb > 1 or tb < 0):
        return False # only intersection is on the infinite line

    return True


def point_intersection(px, py, x1, y1, x2, y2): # return true if the point is on the line / on one of the line's endpoints
# https://lucidar.me/en/mathematics/check-if-a-point-belongs-on-a-line-segment/
# TODO: this doesn't work >:(
    a = np.array([x1, y1])
    b = np.array([x2, y2])
    c = np.array([px, py])

    ab = b - a
    ac = c - a

    if np.cross(ab, ac) != 0:
        return False

    kac = np.dot(ab, ac)
    kab = np.dot(ab, ab)

    if (kac <= kab) and (kac >= 0):
        return True

    return False


def angularResolution_calc(n, G):
    # neighbors of input node
    E = [np.array([G.nodes[i]['x'], G.nodes[i]['y']]) for i in G.neighbors(n)]
    origin = np.array([G.nodes[n]['x'], G.nodes[n]['y']])

    # sort neighbors so they are in a counter-clockwise order around n
    def getAngle(vec):
        newVec = vec - origin
        cosine = newVec[0] / np.linalg.norm(newVec)
        return np.arccos(cosine)
    sortedPoints = sorted(E, key=getAngle)

    sum = 0
    for i in range(0, len(sortedPoints) - 1): # between i and i + 1
        angle = calc_smallest_angle(sortedPoints[i][0], sortedPoints[i][1], origin[0], origin[1], sortedPoints[i + 1][0], sortedPoints[i + 1][1])
        sum += abs(((2*math.pi) / len(sortedPoints)) - angle)
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
        length = math.hypot(G.nodes[e[0]]['x'] - G.nodes[e[1]]['x'], G.nodes[e[0]]['y'] - G.nodes[e[1]]['y'])
        sum += abs((length / l) - 1)
    return sum


def balancedEdgeLength(G): # penalizing stations with degree two that have incident edges with unbalanced lengths
    sum = 0
    for n in G.nodes():
        E = list(G.edges(n))
        if len(E) == 2:
            e_one = math.hypot(G.nodes[E[0][0]]['x'] - G.nodes[E[0][1]]['x'], G.nodes[E[0][0]]['y'] - G.nodes[E[0][1]]['y'])
            e_two = math.hypot(G.nodes[E[1][0]]['x'] - G.nodes[E[1][1]]['x'], G.nodes[E[1][0]]['y'] - G.nodes[E[1][1]]['y'])
            sum += abs(e_one - e_two)
    return sum


def lineStraightness_calc(n, G):
    sum = 0
    E = G.edges(n, data=True)

    if (len(E) > 1):
        # get majors that go through n
        lines = [i[2]['major'] for i in E]

        # iterate through majors, isolate the edges of that major, and perform the angle calculation
        for l in lines:
            e12 = [i for i in E if i[2]['major'] == l]
            if len(e12) == 2: # not a terminating node for this line
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

                angle = calc_smallest_angle(G.nodes[n1]['x'], G.nodes[n1]['y'], G.nodes[n]['x'], G.nodes[n]['y'], G.nodes[n2]['x'], G.nodes[n2]['y'])

                if (angle == 180):
                    angle = 0
                elif (angle > 90):
                    angle = (180 - angle)

                sum += angle

    return sum


def lineStraightness(G): # Edges that form part of a line should, where possible, be collinear either side of each station that the line passes through
    sum = 0
    for n in G.nodes():
        sum += lineStraightness_calc(n, G)
    return sum


def edgeCrossings(G): # edges should cross each other as little as possible, so we count how many pairs of edges intersect -- added from thesis copy
    sum = 0
    edge_pairs = list(itertools.combinations(G.edges(), 2))
    for pair in edge_pairs:
        if line_intersection(G.nodes[pair[0][0]]['x'], G.nodes[pair[0][0]]['y'], G.nodes[pair[0][1]]['x'], G.nodes[pair[0][1]]['y'], G.nodes[pair[1][0]]['x'], G.nodes[pair[1][0]]['y'], G.nodes[pair[1][1]]['x'], G.nodes[pair[1][1]]['y']):
            sum += 1
    return sum


def nodeOcclusion(G): # nodes should not cross edges that are not their own -- NEW
    sum = 0
    for n in G.nodes():
        for e in G.edges():
            if (n not in e) and point_intersection(G.nodes[n]['x'], G.nodes[n]['y'], G.nodes[e[0]]['x'], G.nodes[e[0]]['y'], G.nodes[e[1]]['x'], G.nodes[e[1]]['y']):
                sum += 1
    return sum


def octilinearity(G): # Each edge should be drawn horizontally, vertically, or diagonally at 45 degree
    sum = 0
    for e in G.edges():
        if abs(G.nodes[e[0]]['x'] - G.nodes[e[1]]['x']) != 0:
            sum += abs(math.sin(4 * math.atan(abs(G.nodes[e[0]]['y'] - G.nodes[e[1]]['y']) / abs(G.nodes[e[0]]['x'] - G.nodes[e[1]]['x']))))
    return sum


def calcStationCriteria(G): # The criteria evaluate to a lower value when improved
    return 30000*angularResolution(G) + 50*edgeLength(G) + 45*balancedEdgeLength(G) + 220*lineStraightness(G) + 100*edgeCrossings(G) + 9250*octilinearity(G)


def findNewLocation(n, G, height, width, r, mno):
    initialx = G.nodes[n]['x']
    initialy = G.nodes[n]['y']

    # create a list of new locations in radius that are in bounds
    possible = []
    for x in range((initialx - r), (initialx + (r + 1))):
        for y in range((initialy - r), (initialy + (r + 1))):
            if (x != initialx) and (y != initialy) and (x > 0 and x < height) and (y > 0 and y < height):
                possible.append((x, y))

    # remove locations with oclusions (point exists on top of existing station or edge not connected to this node)
    toremove = []
    for i in possible:
        # check if it intersects with an edge that is not already one of the node's edges / a node
        for e in G.edges():
            if (n not in e) and point_intersection(i[0], i[1], G.nodes[e[0]]['x'], G.nodes[e[0]]['y'], G.nodes[e[1]]['x'], G.nodes[e[1]]['y']):
                toremove.append(i)

    possible = [i for i in possible if i not in toremove]

    # calculate criteria on all possible new locations, saving lowest value/coordinate
    lowestCriteria = mno
    newx = initialx
    newy = initialy

    for p in possible:
        G.nodes[n]['x'] = p[0]
        G.nodes[n]['y'] = p[1]
        criteria = calcStationCriteria(G)

        if (criteria < lowestCriteria):
            lowestCriteria = criteria
            newx = p[0]
            newy = p[1]

    return newx, newy


def clusterOverlengthEdges(G): # TODO
    return []


def clusterBends(G): # TODO return a list
    return []


def clusterPartitions(G): # TODO return a list
    return []


def moveCluster(p): # TODO
    pass


def assign_initial_coordinates(G, height, width): # create an initial layout -- assign x and y coordinates to graph on a grid
    # TODO: randomize start positions / put nodes with the most neighbors at the center?
    xpos = {}
    ypos = {}
    x = 4
    y = 4
    for n in G.nodes():
        xpos[n] = x
        ypos[n] = y

        if (x == width):
            x = 4
            y += 4
        else:
            x += 4
    nx.set_node_attributes(G, xpos, 'x')
    nx.set_node_attributes(G, ypos, 'y')
    return G


def assign_coordinates(G):
    height = 16
    width = math.floor(G.number_of_nodes() / ((height / 4) - 1)) * 4
    G = assign_initial_coordinates(G, height, width)

    # calculate initial layout fitness
    mto = calcStationCriteria(G)

    running = True
    r = 8

    while running:
        # stations
        for v in G.nodes():
            mno = calcStationCriteria(G)
            x, y = findNewLocation(v, G, height, width, r, mno)
            if (x, y) != (G.nodes[v]['x'], G.nodes[v]['y']):
                G.nodes[v]['x'] = x
                G.nodes[v]['y'] = y

        # TODO: station clusters
        # P = clusterOverlengthEdges(G) + clusterBends(G) + clusterPartitions(G)
        # for p in P
        #     mno = calcStationCriteria(G)
        #     mn = findLowestStationCriteria(G)
        #     if mn < mno:
        #         moveCluster(p)

        # TODO: labels

        # TODO: check out cooling vs this
        # mt = calcStationCriteria(G)
        # if not mt < mto:
        #     running = False
        # else:
        #     mto = mt

        r -= 1

        if (r == 0):
            running = False

    return G


# # TESTING
# # create graph
# G = nx.MultiDiGraph()
#
# # add some test nodes
# G.add_node("MATH 221")
# G.add_node("MATH 231")
# G.add_node("MATH 241")
# G.add_edge("MATH 221", "MATH 231", major="Every engineering ever")
# G.add_edge("MATH 231", "MATH 241", major="Every engineering ever")
# G.add_edge("MATH 221", "MATH 231", major="Stats")
# G.add_edge("MATH 231", "MATH 241", major="Stats")
# G.add_edge("MATH 231", "MATH 241", major="Math?")
# G = assign_coordinates(G)
# json = json.dumps(json_graph.node_link_data(G))
# open("graph.json", "a").write(json)

# load in prereqs csv from https://github.com/illinois/prerequisites-dataset (so we only do this once)
prereqs = {}
prereq_table = pd.read_csv("uiuc-prerequisites.csv", header = 0)
for x in range(0, len(prereq_table.index)):
    prereqs[prereq_table.loc[x, 'Course']] = []
    for y in range(0, int(prereq_table.loc[x, 'PrerequisiteNumber'])):
        prereqs[prereq_table.loc[x, 'Course']].append(prereq_table.loc[x, str(y)])

G = read_in_files("majors", prereqs)

# run coordinate algoritm
G = assign_coordinates(G)

# create json file from graph
json = json.dumps(json_graph.node_link_data(G))
open("graph.json", "a").write(json)
