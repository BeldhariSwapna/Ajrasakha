import { FirebaseAuthService } from "#root/modules/auth/services/FirebaseAuthService.js";
import { getFromContainer } from "routing-controllers";
import { appConfig } from '#root/config/app.js';

export async function authorizationChecker(action): Promise<boolean> {
  const token = action.request.headers.authorization?.split(' ')[1];
  if (!token) {
    return false; // No token provided
  }

  // Dev mode bypass: skip Firebase token verification
  if (appConfig.isDevelopment) {
    return true;
  }

  try {
    const firebaseAuthService = getFromContainer(FirebaseAuthService);
    const decoded = await firebaseAuthService.getCurrentUserFromToken(token)
    if (decoded.role === 'moderator' || decoded.role === 'expert') {
      if (decoded.status === 'in-active') {
        return false
      }
    } else if (decoded.isBlocked) {
      return false
    }
    if (!decoded?.firebaseUID) {
      return false
    }
  }
  catch (error) {
    console.error('Authorization error:', error);
    return false; // Invalid token or user not found
  }
  return true; // Authorization successful
}
