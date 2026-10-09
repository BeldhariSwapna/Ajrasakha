import { getAnalytics } from "firebase/analytics";
import {
  signInWithEmailAndPassword,
  signOut,
  createUserWithEmailAndPassword,
  updateProfile,
  EmailAuthProvider,
  reauthenticateWithCredential,
  updatePassword,
} from "firebase/auth";
import { app, auth, googleProvider } from "@/config/firebase";
import { useAuthStore } from "@/stores/auth-store";
import { UserService } from "@/hooks/services/userService";
import { AuthService } from "@/hooks/services/authService";
import { isDevelopment } from "@/shared/app";
const authService = new AuthService();

const userService = new UserService()
export const loginWithEmail = async (email: string, password: string) => {
  try {
    const user = await userService.Getuser(email)
    const isModeratorOrExpert = user?.role === "moderator" || user?.role === "expert";
    const deniedLogin = isModeratorOrExpert ? user?.status === "in-active" : !!user?.isBlocked;
    if (deniedLogin) {
      throw new Error("User marked as Inactive Please Contact Moderator")
    }
    if (!deniedLogin || user === null) {
      const result = await signInWithEmailAndPassword(auth, email, password);

      if (!result.user.emailVerified && !isDevelopment) {
        try {
          await authService.resendVerification(email);
        } catch (resendError) {
          console.error("Failed to trigger verification resend:", resendError);
        }

        await signOut(auth);
        throw new Error("Please verify your email before logging in. A new verification link has been sent to your email.");
      }

      const idToken = await result.user.getIdToken();
      const syncResponse = await authService.accountSync(idToken);

      return Object.assign(result, { appUser: syncResponse?.user });
    }
  } catch (error: unknown) {
    if (error instanceof Error && (error.message === "User marked as Inactive Please Contact Moderator" || error.message === "Please verify your email before logging in.")) {
      throw error;
    }
    if (error instanceof Error && (error.message.includes("Request failed") || error.message.includes("Failed to"))) {
      try {
        const result = await signInWithEmailAndPassword(auth, email, password);
        const idToken = await result.user.getIdToken();
        const syncResponse = await authService.accountSync(idToken);
        return Object.assign(result, { appUser: syncResponse?.user });
      } catch (authError) {
        throw authError;
      }
    }
    throw error;
  }
};

export const createUserWithEmail = async (
  email: string,
  password: string,
  displayName?: string
) => {
  const userCredential = await createUserWithEmailAndPassword(
    auth,
    email,
    password
  );

  if (displayName && userCredential.user) {
    await updateProfile(userCredential.user, {
      displayName,
    });
  }

  return userCredential;
};

export const logout = () => {
  signOut(auth);
  useAuthStore.getState().clearUser();
};

export const verifyCurrentPassword = async (
  email: string,
  currentPassword: string
) => {
  if (!auth.currentUser) throw new Error("User not logged in");

  const credential = EmailAuthProvider.credential(email, currentPassword);

  try {
    await reauthenticateWithCredential(auth.currentUser, credential);
    return { success: true };
  } catch (error) {
    return { success: false, error };
  }
};

export const updateUserPassword = async (newPassword: string) => {
  if (!auth.currentUser) throw new Error("User not logged in");

  try {
    await updatePassword(auth.currentUser, newPassword);
    return { success: true };
  } catch (error) {
    return { success: false, error };
  }
};

let analytics: ReturnType<typeof getAnalytics> | null = null;
try {
  if (app) analytics = getAnalytics(app);
} catch (e) {
  console.warn("Firebase analytics not available:", e);
}
export { analytics };
