import Cookies from 'js-cookie';

const TOKEN_KEY = 'auth_token';

export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;

  // Try localStorage first, fallback to cookie
  return localStorage.getItem(TOKEN_KEY) || Cookies.get(TOKEN_KEY) || null;
};

export const setToken = (token: string): void => {
  if (typeof window === 'undefined') return undefined;

  // Store in both for flexibility
  localStorage.setItem(TOKEN_KEY, token);
  Cookies.set(TOKEN_KEY, token, { expires: 7 }); // 7 days
};

export const removeToken = (): void => {
  if (typeof window === 'undefined') return undefined;

  localStorage.removeItem(TOKEN_KEY);
  Cookies.remove(TOKEN_KEY);
};

export const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp < Date.now() / 1000;
  } catch {
    return true;
  }
};
