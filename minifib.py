
import json
import datetime

now = datetime.datetime.now()

rows = {}
row = { }
row['systemtime'] = now.strftime('%m/%d/%Y %H:%M:%S')
year = now.year
month = now.month


json_string = json.dumps(rows)
print (json_string)
