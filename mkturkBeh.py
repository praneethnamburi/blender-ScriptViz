import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import arrow

cred = credentials.Certificate(os.path.realpath('./_auth/mkturk-sandbox-ce2c5-072282ca7900.json'))
firebase_admin.initialize_app(cred)

db = firestore.client()

# get data from Sausage between July 06 and July 08, 2018
startDate = int(str(arrow.get(2018, 7, 6).timestamp) + '000') # inclusive of start date
endDate = int(str(arrow.get(2018, 7, 9).timestamp) + '000') # not inclusive of end date
docs = db.collection('data')\
        .where('Agent', '==', 'Sausage')\
        .where('Doctype', '==', 'task')\
        .where('CurrentDateValue', '>', startDate)\
        .where('CurrentDateValue', '<', endDate)\
        .limit(100)\
        .get()

# download data files from the entire query
# Note, once you download the data, you need to re-generate the query.
a = [k.to_dict() for k in list(docs)]

# download data one file at a time
a = []
i = 0
for doc in docs:
    print(doc.id)
    thisContent = doc.to_dict()
    a.append(thisContent)
    i = i+1
    if i < 10:
        continue
    if i > 10:
        break
