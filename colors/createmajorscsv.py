import pandas as pd
import json

with open('engmajors.json') as json_file:
    data = json.load(json_file)

df = pd.DataFrame(columns=['Title', 'College', 'Color'])

i = 0
for major in data['Majors']:
    if major['courses'] != []:
        df.loc[i] = [major['title'], major['college'], '#']
        i += 1

df.to_csv('majorcolors.csv', index=False, header=True)
