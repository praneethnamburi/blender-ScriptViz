# import os
# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import firestore
# import arrow
# from timeit import default_timer as timer

# cred = credentials.Certificate(os.path.realpath('./_auth/mkturk-sandbox-ce2c5-072282ca7900.json'))
# firebase_admin.initialize_app(cred)

# db = firestore.client()

# # get data from Sausage between July 06 and July 08, 2018
# startDate = int(str(arrow.get(2019, 2, 1).timestamp) + '000') # inclusive of start date
# endDate = int(str(arrow.get(2019, 2, 5).timestamp) + '000') # not inclusive of end date
# docs = db.collection('data')\
#         .where('Agent', '==', 'Sausage')\
#         .where('Doctype', '==', 'task')\
#         .where('CurrentDateValue', '>', startDate)\
#         .where('CurrentDateValue', '<', endDate)\
#         .limit(100)\
#         .get()

# # download data files from the entire query
# # Note, once you download the data, you need to re-generate the query.
# start = timer()
# a = [k.to_dict() for k in list(docs)]
# [print(k.id) for k in a]
# end = timer()
# print(end-start)

import json
import subprocess

subprocess.call(['node', 'testjs.js'])
tmp1 = json.loads(open('temp.json').read())

a = 1