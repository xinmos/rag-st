import { apiClient } from './client';
import type { BaseResponse, LoginRequest, LoginResponse, User } from '../types';

export const userApi = {
  /**
   * User login
   */
  login: (data: LoginRequest) =>
    apiClient.post<BaseResponse<LoginResponse>>('/api/v1/user/login', data),

  /**
   * Create user
   */
  create: (data: { username: string; email: string; password: string }) =>
    apiClient.post<BaseResponse<User>>('/api/v1/user/create', data),

  /**
   * Get current user info
   */
  getCurrentUser: () =>
    apiClient.post<BaseResponse<User>>('/api/v1/user/me'),

  /**
   * Update current user profile (username and email, not password)
   */
  updateProfile: (data: { username?: string; email?: string }) =>
    apiClient.post<BaseResponse<User>>('/api/v1/user/me/update', data),

  /**
   * Change password (requires current password verification)
   */
  changePassword: (data: { current_password: string; new_password: string }) =>
    apiClient.post<BaseResponse<{ success: boolean }>>('/api/v1/user/me/change-password', data),

  /**
   * Get user list
   */
  list: (params: { skip?: number; limit?: number }) =>
    apiClient.post<BaseResponse<{ total: number; items: User[] }>>('/api/v1/user/list', params),

  /**
   * Get user by ID
   */
  getById: (user_id: number) =>
    apiClient.post<BaseResponse<User>>('/api/v1/user/get', null, { params: { user_id } }),

  /**
   * Update user by ID
   */
  updateById: (user_id: number, data: { username?: string; email?: string; password?: string }) =>
    apiClient.post<BaseResponse<User>>('/api/v1/user/update', data, { params: { user_id } }),

  /**
   * Delete user by ID
   */
  deleteById: (user_id: number) =>
    apiClient.post<BaseResponse<{ deleted: boolean }>>('/api/v1/user/delete', null, { params: { user_id } }),
};
