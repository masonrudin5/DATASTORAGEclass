## MASON RUDIN m285640

print(6.1)
from mydb import db

print (6.2)

query = """SELECT DISTINCT shape
            FROM ufo
            WHERE shape IS NOT NULL"""

df, error = db.querydf(query)

print(df)

print(6.3)

sorted = df.sort_values(by='shape')
print(sorted)




print(7.1)
import pandas as pd
## The dictionary needs to be a list of lists. make a dictionary then cycle through data
##see if this is index 1, then see if the category is already in the dictionarr - if it is append the
## the row, if it is not either of those then add at the end
"""
1. 
cetegory = row[1]

2.
if category not in result:
    result[category] = []

    append full for to list for that key
"""

def by_country(country):
    result = {}
    query = """SELECT *
            FROM ufo
            WHERE country = %s"""

    column_info, data, insert_id, error = db.query(query, [country,])
    for row in data:
        state = row[2]
        if state not in result:
              result[state] = []
              result[state].append(row)
        else:
             result[state].append(row)

    return result

print(7.3)
final_list = by_country('us')
state = final_list['dc']
for item in state:
     print(item)


