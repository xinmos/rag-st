import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { userApi } from '@/lib/api';
import { setToken, removeToken, getToken } from '@/lib/utils/token';
import type { User, LoginRequest } from '@/lib/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: null,  // 将在客户端初始化时设置
  isAuthenticated: false,  // 将在客户端初始化时设置
  isLoading: true,  // 开始时设为 true，等待客户端初始化
  error: null,
};

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await userApi.login(credentials);
      const data = response.data as any;
      const { access_token, user } = data;

      // Store token
      setToken(access_token);

      return { token: access_token, user };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || '登录失败');
    }
  }
);

export const logoutUser = createAsyncThunk('auth/logout', async () => {
  removeToken();
  return null;
});

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const response = await userApi.getCurrentUser();
      return response.data as any;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || '获取用户信息失败');
    }
  }
);

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    initializeAuth: (state, action: PayloadAction<{ token: string | null; isAuthenticated: boolean }>) => {
      state.token = action.payload.token;
      state.isAuthenticated = action.payload.isAuthenticated;
      state.isLoading = false;  // 初始化完成
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.isAuthenticated = true;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      })
      // Logout
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
      })
      // Get current user
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload;
      });
  },
});

export const { clearError, initializeAuth } = authSlice.actions;
export default authSlice.reducer;
