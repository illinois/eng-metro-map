# subway-map
This repo contains the codebase for the [Grainger Engineering Metro Map project](https://d7.cs.illinois.edu/projects/Grainger-Engineering-Metro-Map/). Namely:
- The metro map coordinate generation algorithm (generate-graph/nongeosubwaygenerator.py)
- The d3 engine to create a metro map style diagram from a graph representation (js/visualization.js)

## The algorithm
The metro map generation algorithm is heavily based on the algorithm outlined in "Automatic Metro Map Layout Using Multicriteria Optimization" (Stott, J. et al), with modifications of my own. It is implemented in python, utilizing networkx.
