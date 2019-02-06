console.log("Hello!")

const admin = require('firebase-admin');
var fs = require('fs');

var serviceAccount = require('./_auth/mkturkNode-sandbox-ce2c5-locqz-cbd9fe14f8.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

var db = admin.firestore();

startDate = new Date(2019, 2-1, 1).valueOf(); //month is 0-indexed
endDate = new Date(2019, 2-1, 5).valueOf(); //month is 0-indexed

var query = db.collection('data')
  .where('Agent', '==', 'Sausage')
  .where('Doctype', '==', 'task')
  .where('CurrentDateValue', '>=', startDate)
  .where('CurrentDateValue', '<=', endDate)

console.time("fetch time")

var getDoc = query.get()
  .then(snapshot => {
    if (snapshot.empty) {
      console.log('No matching documents.');
      return;
    }
    var myObj = {};
    snapshot.forEach(doc => {
      myObj[doc.id] = doc.data();
      console.log(doc.id);
    });
    fs.writeFile('./temp.json', JSON.stringify(myObj), 'utf-8', err => {
      if (err) throw err;
      console.log('Write complete!');
    }
    );
    console.timeEnd("fetch time");
  })

