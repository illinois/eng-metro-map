import os
import re
import pandas as pd
import json
import datetime
from nongeosubwaygenerator import *

def containsCourseCodes(st):
    codes = re.findall(r'[A-Z]{2,4}\s\d{3}', st)
    return [c.replace('\xa0', ' ') for c in codes]


def create_major_csv(foldr_name): # makes a csv with the title of every major and a color column, using the files from the specified folder
    df = pd.DataFrame(columns=['Title', 'Color'])

    i = 0
    for entry in os.scandir(foldr_name):
        if entry.path.endswith(".txt"):
            major_title = entry.path[(len(foldr_name) + 1):-4]
            df.loc[i] = [major_title, '#']
            i += 1

    df.to_csv('majorcolors.csv', index=False, header=True)


def read_in_files(foldr_name):
    G = nx.MultiGraph()

    for entry in os.scandir(foldr_name):
        if entry.path.endswith(".txt"):
            major_title = entry.path[(len(foldr_name) + 1):-4]
            lines = open(entry.path, "r").readlines()

            # create a list of courses that does not include elective categories
            courses = []
            parentheses = 0
            for line in lines:
                if (parentheses == 1) and ((re.match(r'"[A-Z]{2,4}\s\d{3}"\sAND\s"[A-Z]{2,4}\s\d{3}"|"[A-Z]{2,4}\s\d{3}"\sOR\s"[A-Z]{2,4}\s\d{3}"', line) != None) or (re.match(r'"[A-Z]{2,4}\s\d{3}"\sAND\s"[A-Z]{2,4}\s\d{3}"|"[A-Z]{2,4}\s\d{3}"\sOR\s"[A-Z]{2,4}\s\d{3}"', line[1:]) != None)): # check if line contains "CODE" OR/AND "CODE"
                    c = containsCourseCodes(line)
                    # if the two codes are MATH 220 and MATH 221, save as MATH 221
                    if ("MATH 221" in c) and ("MATH 220" in c):
                        courses.append("MATH 221")
                    elif "AND" in line: # if AND add both in order
                        courses.extend(c)
                    else: # if OR save in list as "(CODE, CODE)"
                        courses.append(c)

                if "(" in line:
                    parentheses += line.count("(")

                if parentheses == 1:
                    # if the line contains one code, get course code from line
                    c = containsCourseCodes(line)

                    if (len(c) == 1):
                        courses.append(c[0])
                    # otherwise, we don't care

                if ")" in line:
                    parentheses -= line.count(")")

            print(major_title)
            print(courses)

            # add each course to nodes (if dne), and add an edge to the next node
            for x in range(0, len(courses)):
                if isinstance(courses[x], list):
                    for c in courses[x]:
                        if not G.has_node(c): # add node to graph
                            G.add_node(c)

                        if x != (len(courses) - 1): # add edges to graph
                            if isinstance(courses[x + 1], list):
                                for cnext in courses[x + 1]:
                                    G.add_edge(c, cnext, major=major_title)
                            else:
                                G.add_edge(c, courses[x + 1], major=major_title)
                else:
                    if not G.has_node(courses[x]): # add node to graph
                        G.add_node(courses[x])

                    if x != (len(courses) - 1): # add edges to graph
                        if isinstance(courses[x + 1], list):
                            for cnext in courses[x + 1]:
                                G.add_edge(courses[x], cnext, major=major_title)
                        else:
                            G.add_edge(courses[x], courses[x + 1], major=major_title)

    return G


file_name = str(datetime.datetime.now().time()) + "CoEgraph"
G = read_in_files("major")

# modified to save a snapshot of every iteration
os.mkdir(file_name)

# run coordinate algoritm
G = assign_coordinates(G, 100, 100, 10, file_name) # G, scale, r, iterations, foldr_name

# create json file from graph
j = json.dumps(json_graph.node_link_data(G))
open((file_name + ".json"), "w").write(j)
