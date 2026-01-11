'use client';

import { Provider } from 'react-redux';
import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { store } from './store';
import { getToken } from '@/lib/utils/token';
import { initializeAuth } from './slices/authSlice';

export function StoreProvider({ children }: { children: ReactNode }) {
  // 客户端初始化：从 localStorage 读取 token
  useEffect(() => {
    const token = getToken();
    if (token) {
      store.dispatch(initializeAuth({ token, isAuthenticated: true }));
    } else {
      store.dispatch(initializeAuth({ token: null, isAuthenticated: false }));
    }
  }, []);

  return <Provider store={store}>{children}</Provider>;
}
