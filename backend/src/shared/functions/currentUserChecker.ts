import {FirebaseAuthService} from '#root/modules/auth/services/FirebaseAuthService.js';
import {getFromContainer, UnauthorizedError} from 'routing-controllers';
import {CurrentUserChecker} from 'routing-controllers';
import {Request} from 'express';
import {IUser} from '../interfaces/models.js';
import {appConfig} from '#root/config/app.js';

const DEV_USER_ID = '000000000000000000000001';

export const currentUserChecker: CurrentUserChecker = async (
  action,
): Promise<IUser | null> => {
  const request = action.request as Request;

  const token = request.headers.authorization?.split(' ')[1];
  if (!token) {
    return null;
  }

  // Dev mode bypass: return a stub user without Firebase verification
  if (appConfig.isDevelopment) {
    return {
      _id: DEV_USER_ID as any,
      firebaseUID: 'dev-firebase-uid',
      firstName: 'Dev',
      lastName: 'User',
      email: 'dev@ajrasakha.local',
      role: 'admin' as any,
      isBlocked: false,
      status: 'active' as any,
    } as IUser;
  }

  try {
    const authService = getFromContainer(FirebaseAuthService);
    const user = await authService.getCurrentUserFromToken(token);

    if (!user) {
      throw new UnauthorizedError('Invalid token or user not found');
    }

    return user;
  } catch (err) {
    throw new UnauthorizedError('Failed to authenticate user');
  }
};
