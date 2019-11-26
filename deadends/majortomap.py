import networkx as nx
import json
import pandas as pd
import math
import random
import matplotlib.pyplot as plt

class Node:
    def __init__(self, coords):
        self.coords = coords


class Station:
    def __init__(self, label):
        self.label = label


class Line:
    def __init__(self, label, color):
        self.label = label
        self.name = label.replace(" ", "")
        self.color = color
        self.shiftCoords = [0, 0]
        self.nodes = []


class TubeMap:
    def __init__(self):
        self.stations = {}
        self.lines = []


def findDir(pointOne, pointTwo):
    if (pointTwo[0] - pointOne[0]) == 0: # vertical line
        if pointTwo[1] > pointOne[1]:
            return "N"
        else:
            return "S"

    slope = (pointTwo[1] - pointOne[1]) / (pointTwo[0] - pointOne[0])
    if slope >= (1 / math.sqrt(2)) or slope <= (-1 / math.sqrt(2)):
        if pointTwo[1] > pointOne[1]:
            return "N"
        else:
            return "S"
    else:
        if pointTwo[0] > pointOne[0]:
            return "E"
        else:
            return "W"


# import json data
with open('engmajors.json') as json_file:
    data = json.load(json_file)

# dictionary to save major start points, object for final data
start = {}
majorMap = TubeMap()
majorcolors = pd.read_csv('majorcolors.csv', header=0)

# create graph from data and station attribute for each class
graph = nx.MultiDiGraph()
for major in data['Majors']:
    currCourse = '';
    prevCourse = '';

    for course in major['courses']:
        if isinstance(course, str):
            currCourse = course.replace(" ", "")
            if currCourse not in majorMap.stations:
                majorMap.stations[currCourse] = Station(course)
        else:
            currCourse = major['title'].replace(" ", "") + ":" + course['title'].replace(" ", "")
            if currCourse not in majorMap.stations:
                majorMap.stations[currCourse] = Station(course['title'])

        graph.add_node(currCourse)

        if (prevCourse != ''):
            graph.add_edge(prevCourse, currCourse, major=major['title'], college=major['college'])
        else:
            start[major['title']] = currCourse

        prevCourse = currCourse

# find coordinates
pos = nx.spectral_layout(graph, scale=50, center=[0, 0])
# nx.draw_spectral(graph)
# plt.show()

# create line object for each major
for major in data['Majors']:
    line = Line(major['title'], majorcolors.loc[majorcolors['Title'] == major['title']].iat[0, 1])

    nodes = []
    for course in major['courses']:
        if isinstance(course, str):
            coords = [math.floor(c) for c in pos[course.replace(" ", "")]]
            n = Node(coords)
            n.name = course.replace(" ", "")
            n.labelPos = 'E'
            nodes.append(n)
        else:
            courseTitle = major['title'].replace(" ", "") + ":" + course['title'].replace(" ", "")
            coords = [math.floor(c) for c in pos[courseTitle]]
            n = Node(coords)
            n.name = courseTitle
            n.labelPos = 'E'
            nodes.append(n)

    # add points to maintain 45/90 degree turns
    finalNodes = []
    for x in range(0, len(nodes)):
        if x < 2:
            finalNodes.append(nodes[x])
            continue

        pointOne = finalNodes[len(finalNodes) - 2].coords # a, b
        pointTwo = finalNodes[len(finalNodes) - 1].coords # m, n
        pointThree = nodes[x].coords # x, y
        pointFour = None

        if (x < len(nodes) - 1):
            pointFour = nodes[x + 1].coords

        # if point three makes a straight line with the previous 2, add point
        # (𝑛 - 𝑏)(𝑥 - 𝑚) = (𝑦 - 𝑛)(𝑚 - 𝑎)
        if ((pointTwo[1] - pointOne[1])*(pointThree[0] - pointTwo[0])) == ((pointThree[1] - pointTwo[1])*(pointTwo[0] - pointOne[0])):
            finalNodes.append(nodes[x])
            continue
        else:
            # find all points that could be added to make a 45/90 degree turn
            points = []
            # 45 degree:
            points.append([(pointTwo[0] + 1), (pointTwo[1] + 2)])
            points.append([(pointTwo[0] - 1), (pointTwo[1] + 2)])
            points.append([(pointTwo[0] + 1), (pointTwo[1] - 2)])
            points.append([(pointTwo[0] - 1), (pointTwo[1] - 2)])
            points.append([(pointTwo[0] + 2), (pointTwo[1] + 1)])
            points.append([(pointTwo[0] - 2), (pointTwo[1] + 1)])
            points.append([(pointTwo[0] + 2), (pointTwo[1] - 1)])
            points.append([(pointTwo[0] - 2), (pointTwo[1] - 1)])
            # 90 degree:
            points.append([(pointTwo[0] + 1), (pointTwo[1] + 1)])
            points.append([(pointTwo[0] - 1), (pointTwo[1] + 1)])
            points.append([(pointTwo[0] + 1), (pointTwo[1] - 1)])
            points.append([(pointTwo[0] - 1), (pointTwo[1] - 1)])

            # if point three is one of these points
            if pointThree in points:
                i = points.index(pointThree)
                # if 45 degree, (i between 0 and 7) add point
                if (i < 8):
                    finalNodes.append(nodes[x])
                    continue
                else:
                    nodes[x].dir = findDir(pointOne, pointTwo)
                    finalNodes.append(nodes[x])
                    continue
            else:
                # check if any of these points is in line with point four
                if pointFour:
                    for i in range(0, len(points)):
                        if ((points[i][1] - pointThree[1])*(pointFour[0] - points[i][0])) == ((pointFour[1] - points[i][1])*(points[i][0] - pointThree[0])):
                            if (i < 8):
                                finalNodes.append(Node(points[i]))
                                finalNodes.append(nodes[x])
                                continue
                            else:
                                n = Node(points[i])
                                n.dir = findDir(pointTwo, pointThree)
                                finalNodes.append(n)
                                finalNodes.append(nodes[x])
                                continue

                # choose point closest to pointThree, add that point and then the current node
                closestdist = math.sqrt((points[0][0] - pointThree[0])**2 + (points[0][1] - pointThree[1])**2)
                closesti = 0
                for i in range(1, len(points)):
                    dist = math.sqrt((points[i][0] - pointThree[0])**2 + (points[i][1] - pointThree[1])**2)
                    if dist < closestdist:
                        closestdist = dist
                        closesti = i

                if (closesti < 8):
                    finalNodes.append(Node(points[closesti]))
                    finalNodes.append(nodes[x])
                else:
                    n = Node(points[closesti])
                    n.dir = findDir(pointTwo, pointThree)
                    finalNodes.append(n)
                    finalNodes.append(nodes[x])

    line.nodes.extend(finalNodes)
    majorMap.lines.append(line)

# export as json
json_data = json.dumps(majorMap.__dict__, default = lambda o: o.__dict__, indent = 2)

with open("engmap.json", "a") as json_file:
    print("{}".format(json_data), file = json_file)
