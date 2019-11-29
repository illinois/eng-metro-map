import os
import re
import pandas as pd
import json

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


# list to save edges, dictionary to save nodes
edges = []
nodes = {}

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
            if courses[x] not in nodes:
                nodes[courses[x]] = node(courses[x])

            if x != (len(courses) - 1):
                edges.append(edge(courses[x], courses[x + 1], major_title))

# create json file
final = json.dumps({'nodes': [n.__dict__ for n in list(nodes.values())], 'edges': [e.__dict__ for e in edges]})
open("graph.json", "a").write(final)
