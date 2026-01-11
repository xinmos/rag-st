export interface User {
  id: number;
  username: string;
  email: string;
  create_time: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserUpdateRequest {
  username?: string;
  email?: string;
  password?: string;
}
