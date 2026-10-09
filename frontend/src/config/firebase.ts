import { initializeApp, type FirebaseApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, type Auth } from "firebase/auth";
import { resolveEnv } from "./runtime-env";

export const firebaseConfig = {
  apiKey: resolveEnv("VITE_FIREBASE_API_KEY", import.meta.env.VITE_FIREBASE_API_KEY),
  authDomain: resolveEnv(
    "VITE_FIREBASE_AUTH_DOMAIN",
    import.meta.env.VITE_FIREBASE_AUTH_DOMAIN
  ),
  projectId: resolveEnv(
    "VITE_FIREBASE_PROJECT_ID",
    import.meta.env.VITE_FIREBASE_PROJECT_ID
  ),
  storageBucket: resolveEnv(
    "VITE_FIREBASE_STORAGE_BUCKET",
    import.meta.env.VITE_FIREBASE_STORAGE_BUCKET
  ),
  messagingSenderId: resolveEnv(
    "VITE_FIREBASE_MESSAGING_SENDER_ID",
    import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID
  ),
  appId: resolveEnv("VITE_FIREBASE_APP_ID", import.meta.env.VITE_FIREBASE_APP_ID),
  measurementId: resolveEnv(
    "VITE_FIREBASE_MEASUREMENT_ID",
    import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
  ),
};

function stubAuth(): Auth {
  return {
    currentUser: null,
    onAuthStateChanged: (cb: (u: null) => void) => {
      cb(null);
      return () => {};
    },
  } as unknown as Auth;
}

let app: FirebaseApp | undefined;
let auth: Auth;
let googleProvider: GoogleAuthProvider | undefined;

try {
  if (firebaseConfig.apiKey && firebaseConfig.apiKey !== "your-firebase-api-key") {
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    googleProvider = new GoogleAuthProvider();
  } else {
    throw new Error("Firebase API key not configured");
  }
} catch (e) {
  console.warn("Firebase not configured, running without auth:", e);
  auth = stubAuth();
}

export { app, auth, googleProvider };
