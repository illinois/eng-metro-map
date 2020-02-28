import os
import re
import pandas as pd
import json
from nongeosubwaygenerator import *

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
    G = nx.MultiGraph()

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


# # TESTING
# # create graph
# G = nx.MultiGraph()
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
# print(G.nodes(data=True))

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
open("graph.json", "w").write(json)
