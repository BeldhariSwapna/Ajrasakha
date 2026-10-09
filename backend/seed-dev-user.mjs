import { MongoClient } from 'mongodb';
import tls from 'tls';

const uri = 'mongodb://beldhariswapna_db_user:HEjqjavTIAUnxGvR@ac-6b513z1-shard-00-00.lpvctr7.mongodb.net:27017/agriai?retryWrites=true&w=majority&authSource=admin';

const c = new MongoClient(uri, {
  tlsAllowInvalidCertificates: true,
  tlsAllowInvalidHostnames: true,
  secureContext: tls.createSecureContext({ secureProtocol: 'TLSv1_2_method' }),
  serverSelectionTimeoutMS: 15000,
});

async function seed() {
  await c.connect();
  const db = c.db('agriai');
  const users = db.collection('users');

  const existing = await users.findOne({ firebaseUID: 'dev-firebase-uid' });
  if (existing) {
    console.log('Dev user already exists:', existing._id);
    await c.close();
    return;
  }

  const devUser = {
    firebaseUID: 'dev-firebase-uid',
    firstName: 'Dev',
    lastName: 'User',
    email: 'dev@ajrasakha.local',
    role: 'admin',
    isBlocked: false,
    status: 'active',
    phoneNo: '0000000000',
    photoURL: '',
    state: 'Maharashtra',
    district: 'Pune',
    block: 'Haveli',
    village: 'Wanowrie',
    preference: { state: 'Maharashtra', language: 'en' },
    points: 0,
    level: 1,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  const result = await users.insertOne(devUser);
  console.log('Dev user created with _id:', result.insertedId);
  await c.close();
}

seed().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
