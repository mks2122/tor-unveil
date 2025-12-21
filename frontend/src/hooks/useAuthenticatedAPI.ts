import { useMemo } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { createAuthenticatedAPI } from '../services/authService';

/**
 * Custom hook to get an authenticated axios instance
 * Automatically includes the Clerk JWT token in all requests
 */
export const useAuthenticatedAPI = () => {
  const { getToken } = useAuth();

  const api = useMemo(() => {
    return createAuthenticatedAPI(getToken);
  }, [getToken]);

  return api;
};
