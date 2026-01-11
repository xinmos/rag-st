import { useCallback, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from './redux';
import { loginUser, logoutUser, getCurrentUser, clearError } from '@/lib/store/slices/authSlice';

export function useAuth() {
  const dispatch = useAppDispatch();
  const { user, token, isAuthenticated, isLoading, error } = useAppSelector(
    (state) => state.auth
  );

  // Fetch current user on mount if authenticated
  useEffect(() => {
    if (isAuthenticated && !user) {
      dispatch(getCurrentUser());
    }
  }, [isAuthenticated, user, dispatch]);

  const handleLogin = useCallback(
    async (username: string, password: string) => {
      const result = await dispatch(loginUser({ username, password }));
      return {
        success: loginUser.fulfilled.match(result),
        error: result.payload as string | undefined,
      };
    },
    [dispatch]
  );

  const handleLogout = useCallback(() => {
    dispatch(logoutUser());
  }, [dispatch]);

  const clearAuthError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  const refetch = useCallback(() => {
    if (isAuthenticated) {
      dispatch(getCurrentUser());
    }
  }, [dispatch, isAuthenticated]);

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    logout: handleLogout,
    clearError: clearAuthError,
    refetch,
  };
}
