// connect to firebase
const admin = require('firebase-admin');
var serviceAccount = require('./_auth/mkturkNode-sandbox-ce2c5-locqz-cbd9fe14f8.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});
var db = admin.firestore();

//parse input arguments
var v = require('commander')
  .option('-a, --agent [value]', 'Name of the agent', 'Sausage')
  .option('-s, --start-date [value]', 'Start date yyyymmdd', '20190201')
  .option('-e, --end-date [value]', 'End date yyyymmdd', '20190205')
  .option('-o, --output [value]', 'Name of the output file', './temp.json')
  .option('--no-print', 'Print retrieved document IDs')
  .parse(process.argv);

console.log(`Fetching ${v.agent}'s data from ${v.startDate} to ${v.endDate}`);

function parseDate(thisDate){
  var startYear = parseInt(thisDate.slice(0,4));
  var startMonth = parseInt(thisDate.slice(4,6)) - 1;
  var startDay = parseInt(thisDate.slice(6,8));
  return new Date(startYear, startMonth, startDay).valueOf();
}

//set up database query
var query = db.collection('data')
  .where('Agent', '==', v.agent)
  .where('Doctype', '==', 'task')
  .where('CurrentDateValue', '>=', parseDate(v.startDate))
  .where('CurrentDateValue', '<=', parseDate(v.endDate))

//fetch the data and write it to a json file
var fs = require('fs');
console.time("Fetch time")
query
  .get()
  .then(snapshot => {
    if (snapshot.empty) {
      console.log('No matching documents.');
      return;
    }
    var myObj = {};
    snapshot.forEach(doc => {
      myObj[doc.id] = doc.data();
      if (v.print) {
        console.log(doc.id);
      }
    });
    fs.writeFile(v.output, JSON.stringify(myObj), 'utf-8', err => {
      if (err) throw err;
      console.log('Wrote to ' + v.output);
    }
    );
    console.timeEnd("Fetch time");
  })
