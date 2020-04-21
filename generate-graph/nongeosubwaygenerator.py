import networkx as nx
from networkx.readwrite import json_graph
import math
import numpy as np
import itertools
import json

def calc_smallest_angle(x1, y1, x2, y2, x3, y3): # find the smallest angle between meeting line segments where x2, y2 is the vertex
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

    ta = a_num / denom
    tb = b_num / denom

    if (ta > 1 or ta < 0) or (tb > 1 or tb < 0):
        return False # only intersection is on the infinite line

    return True


def point_intersection(px, py, x1, y1, x2, y2): # return true if the point is on the line / on one of the line's endpoints
# https://lucidar.me/en/mathematics/check-if-a-point-belongs-on-a-line-segment/
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


def angular_resolution_calc(n, G):
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


def angular_resolution_node(n, G):
    sum = angular_resolution_calc(n, G)
    for m in G.neighbors(n):
        sum += angular_resolution_calc(m, G)
    return sum


def angular_resolution(G): # The angles of incident edges at each station should be maximized
    sum = 0
    for n in G.nodes():
        sum += angular_resolution_calc(n, G)
    return sum


def edge_length_node(n, G):
    l = 4 # prefered multiple (grid spacing g assumed as 1)

    sum = 0
    for e in G.edges(n):
        length = math.hypot(G.nodes[e[0]]['x'] - G.nodes[e[1]]['x'], G.nodes[e[0]]['y'] - G.nodes[e[1]]['y'])
        sum += abs((length / l) - 1)
    return sum


def edge_length(G): # The edge lengths across the whole map should be approximately equal
    l = 4 # prefered multiple (grid spacing g assumed as 1)

    sum = 0
    for e in G.edges():
        length = math.hypot(G.nodes[e[0]]['x'] - G.nodes[e[1]]['x'], G.nodes[e[0]]['y'] - G.nodes[e[1]]['y'])
        sum += abs((length / l) - 1)
    return sum


def balanced_edge_length_calc(n, G):
    E = list(G.edges(n))
    if len(E) == 2:
        e_one = math.hypot(G.nodes[E[0][0]]['x'] - G.nodes[E[0][1]]['x'], G.nodes[E[0][0]]['y'] - G.nodes[E[0][1]]['y'])
        e_two = math.hypot(G.nodes[E[1][0]]['x'] - G.nodes[E[1][1]]['x'], G.nodes[E[1][0]]['y'] - G.nodes[E[1][1]]['y'])
        return abs(e_one - e_two)
    else:
        return 0


def balanced_edge_length_node(n, G):
    sum = balanced_edge_length_calc(n, G)
    for m in G.neighbors(n):
        sum += balanced_edge_length_calc(m, G)
    return sum


def balanced_edge_length(G): # penalizing stations with degree two that have incident edges with unbalanced lengths
    sum = 0
    for n in G.nodes():
        sum += balanced_edge_length_calc(n, G)
    return sum


def line_straightness_calc(n, G):
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


def line_straightness_node(n, G): # get the line straightness effect from one node
    sum = line_straightness_calc(n, G)
    for m in G.neighbors(n):
        sum += line_straightness_calc(m, G)
    return sum


def line_straightness(G): # Edges that form part of a line should, where possible, be collinear either side of each station that the line passes through
    sum = 0
    for n in G.nodes():
        sum += line_straightness_calc(n, G)
    return sum


def edge_crossings(G): # edges should cross each other as little as possible, so we count how many pairs of edges intersect -- added from thesis copy
    sum = 0
    edge_pairs = list(itertools.combinations(G.edges(), 2))
    for pair in edge_pairs:
        if line_intersection(G.nodes[pair[0][0]]['x'], G.nodes[pair[0][0]]['y'], G.nodes[pair[0][1]]['x'], G.nodes[pair[0][1]]['y'], G.nodes[pair[1][0]]['x'], G.nodes[pair[1][0]]['y'], G.nodes[pair[1][1]]['x'], G.nodes[pair[1][1]]['y']):
            sum += 1
    return sum


def octilinearity_node(n, G):
    sum = 0
    for e in G.edges(n):
        if abs(G.nodes[e[0]]['x'] - G.nodes[e[1]]['x']) != 0:
            sum += abs(math.sin(4 * math.atan(abs(G.nodes[e[0]]['y'] - G.nodes[e[1]]['y']) / abs(G.nodes[e[0]]['x'] - G.nodes[e[1]]['x']))))
    return sum


def octilinearity(G): # Each edge should be drawn horizontally, vertically, or diagonally at 45 degree
    sum = 0
    for e in G.edges():
        if abs(G.nodes[e[0]]['x'] - G.nodes[e[1]]['x']) != 0:
            sum += abs(math.sin(4 * math.atan(abs(G.nodes[e[0]]['y'] - G.nodes[e[1]]['y']) / abs(G.nodes[e[0]]['x'] - G.nodes[e[1]]['x']))))
    return sum


def calc_station_criteria(G): # The criteria evaluate to a lower value when improved
    return 30000*angular_resolution(G) + 50*edge_length(G) + 45*balanced_edge_length(G) + 220*line_straightness(G) + 5000*edge_crossings(G) + 9250*octilinearity(G)


def score_from_node(n, G): # scoring that only includes current node, to speed up processing. Edge crossing is still done on full graph because I can't think of a node dependent way to do that
    return 30000*angular_resolution_node(n, G) + 50*edge_length_node(n, G) + 45*balanced_edge_length_node(n, G) + 220*line_straightness_node(n, G) + 5000*edge_crossings(G) + 9250*octilinearity_node(n, G)


def node_occlusion(n, x, y, G): # determine whether node with given coordinates crosses an edge that is not its own
    for e in G.edges():
        if (n not in e) and (point_intersection(x, y, G.nodes[e[0]]['x'], G.nodes[e[0]]['y'], G.nodes[e[1]]['x'], G.nodes[e[1]]['y'])):
            print(G.nodes[n])
            print(e)
            print(G.nodes[e[0]])
            print(G.nodes[e[1]])
            return True

    for m in G.neighbors(n): # all other nodes taken care of in above case
        if (G.nodes[m]['x'] == x) and (G.nodes[m]['y'] == y):
            print(G.nodes[n])
            print(G.nodes[m])
            return True
    return False


def find_new_location(n, G, height, width, r):
    print("finding locations")
    base = score_from_node(n, G)

    # save initial x and y coordinates
    initialx = G.nodes[n]['x']
    initialy = G.nodes[n]['y']

    # determine whether initial coordinates are on top of other node's edge -- if so they MUST change
    nodeOcc = node_occlusion(n, initialx, initialy, G)

    # create a list of new locations in radius that are in bounds
    possible = []
    for x in range((initialx - r), (initialx + (r + 1))):
        for y in range((initialy - r), (initialy + (r + 1))):
            if (x != initialx) and (y != initialy) and (x > 0 and x < width) and (y > 0 and y < height):
                if not node_occlusion(n, x, y, G):
                    possible.append((x, y))

    # if original node occludes, but list is empty, continue to search for empty spot with no occlusion

    print(possible)

    if nodeOcc and not possible:
        print("ugh a BFS")
        visited = {}
        queue = []

        visited[(initialx, initialy)] = True
        queue.append((initialx, initialy))

        while queue:
            s = queue.pop(0)
            intersects = False

            for e in G.edges(): # check for edge / point overlap
                if (n not in e) and (point_intersection(s[0], s[1], G.nodes[e[0]]['x'], G.nodes[e[0]]['y'], G.nodes[e[1]]['x'], G.nodes[e[1]]['y'])):
                    intersects = True
                    break

            if not intersects:
                for m in G.nodes(): # check for station / point overlap
                    if (s[0] == G.nodes[m]['x']) and (s[1] == G.nodes[m]['y']):
                        intersects = True

                    for f in G.edges(n): # check for station overlap with new edge
                        if (point_intersection(G.nodes[m]['x'], G.nodes[m]['y'], s[0], s[1], G.nodes[f[1]]['x'], G.nodes[f[1]]['y'])):
                            intersects = True
                            break

                    if intersects:
                        break

            if not intersects:
                return s[0], s[1]

            if (s[0] - 1) > 0:
                queue.append((s[0] - 1, s[1]))
                visited[(s[0] - 1, s[1])] = True

            queue.append((s[0], s[1] + 1))
            visited[(s[0], s[1] + 1)] = True

            queue.append((s[0] + 1, s[1]))
            visited[(s[0] + 1, s[1])] = True

            if (s[1] - 1) > 0:
                queue.append((s[0], s[1] - 1))
                visited[(s[0], s[1] - 1)] = True

        print("no spot found!!!")
        return initialx, initialy

    # calculate criteria on all possible new locations, saving lowest value / coordinate

    if nodeOcc:
        G.nodes[n]['x'] = possible[0][0]
        G.nodes[n]['y'] = possible[0][1]
        lowestCriteria = score_from_node(n, G)
        newx = possible[0][0]
        newy = possible[0][1]

        for p in range(1, len(possible)):
            G.nodes[n]['x'] = possible[p][0]
            G.nodes[n]['y'] = possible[p][1]
            criteria = score_from_node(n, G)

            if (criteria < lowestCriteria):
                lowestCriteria = criteria
                newx = possible[p][0]
                newy = possible[p][1]

    lowestCriteria = base
    newx = initialx
    newy = initialy

    for p in possible:
        G.nodes[n]['x'] = p[0]
        G.nodes[n]['y'] = p[1]
        criteria = score_from_node(n, G)

        if (criteria < lowestCriteria):
            lowestCriteria = criteria
            newx = p[0]
            newy = p[1]

    if (newx != initialx) or (newy != initialy):
        print("new spot!")

    return newx, newy


def assign_initial_coordinates(G, scale): # create an initial layout
    # generated_postitions = nx.spring_layout(G, iterations=80, center=[1, 1])
    generated_postitions = nx.kamada_kawai_layout(G, center=[1, 1])
    positions = {}

    for node, pos in generated_postitions.items():
        x = int(round((pos[0] * scale), 0))
        y = int(round((pos[1] * scale), 0))

        if (x, y) in positions.values():
            visited = {}
            queue = []

            visited[(x, y)] = True
            queue.append((x, y))

            while queue:
                s = queue.pop(0)

                if s not in positions.values():
                    positions[node] = (s[0], s[1])
                    break

                if (s[0] - 1) > 0:
                    queue.append((s[0] - 1, s[1]))
                    visited[(s[0] - 1, s[1])] = True

                queue.append((s[0], s[1] + 1))
                visited[(s[0], s[1] + 1)] = True

                queue.append((s[0] + 1, s[1]))
                visited[(s[0] + 1, s[1])] = True

                if (s[1] - 1) > 0:
                    queue.append((s[0], s[1] - 1))
                    visited[(s[0], s[1] - 1)] = True
        else:
            positions[node] = (x, y)

    xpos = {k:v[0] for (k, v) in positions.items()}
    ypos = {k:v[1] for (k, v) in positions.items()}
    height = max(xpos.values())
    width = max(ypos.values())

    nx.set_node_attributes(G, xpos, 'x')
    nx.set_node_attributes(G, ypos, 'y')
    return G, height, width


def assign_coordinates(G, scale, r, iterations, file_name):
    G, height, width = assign_initial_coordinates(G, scale)

    j = json.dumps(json_graph.node_link_data(G))
    open((file_name + "/0.json"), "w").write(j)

    # calculate initial layout fitness
    mto = calc_station_criteria(G)

    running = True
    counter = 1

    while running:
        # stations
        print(len(G))
        for v in G.nodes():
            print("iteration " + str(counter) + " node " + v)
            x, y = find_new_location(v, G, height, width, r)
            G.nodes[v]['x'] = x
            G.nodes[v]['y'] = y

        j = json.dumps(json_graph.node_link_data(G))
        open((file_name + "/" + str(counter) + ".json"), "w").write(j)

        mt = calc_station_criteria(G)
        if (mt > mto):
            print("uh")

        if (not mt < mto) or (counter == iterations):
            running = False
        else:
            mto = mt
            counter += 1

    return G
