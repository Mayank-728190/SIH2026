const { MongoClient } = require('mongodb');
const { faker } = require('@faker-js/faker');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config({ path: '../.env' });

const MONGODB_URI = process.env.MONGODB_URI || "mongodb://localhost:27017";
const MONGODB_DATABASE = process.env.MONGODB_DATABASE || "continuum_db";

const NUM_CUSTOMERS = 1000;
const NUM_TRANSACTIONS = 25000;

const LANGUAGES = ["english", "hindi", "marathi", "tamil", "telugu", "kannada", "bengali"];
const MERCHANTS = ["Amazon", "Flipkart", "Zomato", "Swiggy", "Uber", "Ola", "Reliance Fresh", "DMart", "Netflix", "Spotify", "IRCTC", "MakeMyTrip"];

function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

async function seedData() {
    console.log(`Connecting to MongoDB at ${MONGODB_URI}...`);
    const client = new MongoClient(MONGODB_URI);

    try {
        await client.connect();
        const db = client.db(MONGODB_DATABASE);
        
        console.log("Clearing existing customers and transactions...");
        await db.collection('customers').deleteMany({});
        await db.collection('transactions').deleteMany({});
        
        console.log(`Generating ${NUM_CUSTOMERS} customers...`);
        const customers = [];
        const customerIds = [];
        
        for (let i = 0; i < NUM_CUSTOMERS; i++) {
            const cId = `CUST_${uuidv4().replace(/-/g, '').substring(0, 8).toUpperCase()}`;
            customerIds.push(cId);
            
            const phone = `+91 ${randomInt(6000000000, 9999999999)}`;
            
            customers.push({
                _id: cId,
                id: cId,
                name: faker.person.fullName(),
                phone_number: phone,
                language_preference: LANGUAGES[randomInt(0, LANGUAGES.length - 1)],
                created_at: new Date()
            });
        }
        
        await db.collection('customers').insertMany(customers);
        console.log("Customers inserted.");
        
        console.log(`Generating ${NUM_TRANSACTIONS} transactions...`);
        let transactions = [];
        let totalInserted = 0;
        
        for (let i = 0; i < NUM_TRANSACTIONS; i++) {
            const cId = customerIds[randomInt(0, customerIds.length - 1)];
            const tId = `TXN_${uuidv4().replace(/-/g, '').substring(0, 12).toUpperCase()}`;
            
            const daysAgo = randomInt(0, 365);
            const tTime = new Date();
            tTime.setDate(tTime.getDate() - daysAgo);
            tTime.setMinutes(tTime.getMinutes() - randomInt(0, 1440));
            
            const amount = parseFloat((Math.random() * (15000.0 - 50.0) + 50.0).toFixed(2));
            
            transactions.push({
                _id: tId,
                id: tId,
                customer_id: cId,
                account_id: `ACC_${cId.substring(cId.length - 8)}`,
                amount: amount,
                merchant: MERCHANTS[randomInt(0, MERCHANTS.length - 1)],
                timestamp: tTime,
                status: "COMPLETED"
            });
            
            if (transactions.length === 5000) {
                await db.collection('transactions').insertMany(transactions);
                totalInserted += transactions.length;
                transactions = [];
                console.log(`Inserted ${totalInserted}/${NUM_TRANSACTIONS} transactions...`);
            }
        }
        
        if (transactions.length > 0) {
            await db.collection('transactions').insertMany(transactions);
            totalInserted += transactions.length;
            console.log(`Inserted ${totalInserted}/${NUM_TRANSACTIONS} transactions...`);
        }
        
        console.log("All transactions inserted successfully.");
        console.log("Seeding complete.");
        
    } catch (e) {
        console.error(e);
    } finally {
        await client.close();
    }
}

seedData();
