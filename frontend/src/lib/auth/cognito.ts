import { getApiBaseUrl } from '@/lib/api/auth';

// Types for API responses
interface SignUpResponse {
  user_sub: string;
  confirmed: boolean;
}

interface LoginResponse {
  success: boolean;
  data: {
    access_token: string;
    id_token: string;
    refresh_token?: string | null;
    token_type?: string | null;
    expires_in?: number;
  };
}

interface ConfirmResponse {
  confirmed: boolean;
}

// API Client with error handling
const apiClient = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    // Handle error backend
    const errorMessage = data.detail?.message || data.detail || 'Something went wrong';
    throw new Error(errorMessage);
  }

  return data as T;
};
//Signup call to backend
export const signUp = async (
  email: string,
  password: string,
  firstName: string,
  lastName: string,
  address: string
): Promise<{ userSub: string; confirmed: boolean }> => {//expects to return these back
  try {
    const response = await apiClient<SignUpResponse>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, firstName, lastName, address }),//create JSON for API Post
    });

    return {//Handle API response
      userSub: response.user_sub,
      confirmed: response.confirmed,
    };
  } catch (error) {
    console.error('Signup error:', error);
    throw error;
  }
};

// Login function call to backend 
export const login = async (
  email: string,
  password: string
): Promise<{ accessToken: string; idToken: string; expiresIn: number }> => {//expects to return these
  try {
    const response = await apiClient<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),//Create JSON
    });

    const tokens = response.data;

    return {
      accessToken: tokens.access_token,
      idToken: tokens.id_token,
      expiresIn: tokens.expires_in ?? 0,
    };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

// Confirm Signup function to backend 
export const confirmSignUp = async (
  email: string,
  code: string
): Promise<boolean> => {
  try {
    const response = await apiClient<ConfirmResponse>('/auth/confirm', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    });

    return response.confirmed;
  } catch (error) {
    console.error('Confirmation error:', error);
    throw error;
  }
};

export const resendConfirmationCode = async (email: string): Promise<void> => {
  try {
    await apiClient('/auth/resend-code', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  } catch (error) {
    console.error('Resend code error:', error);
    throw error;
  }
};

// Store tokens 
export const setSession = (tokens: { 
  accessToken: string; 
  idToken: string;
  expiresIn?: number;
}) => {
  if (!tokens.accessToken || !tokens.idToken) {
    throw new Error('Cannot store empty auth tokens');
  }

  localStorage.setItem('accessToken', tokens.accessToken);
  localStorage.setItem('idToken', tokens.idToken);

  if (typeof tokens.expiresIn === 'number') {
    localStorage.setItem('tokenExpiry', String(Date.now() + tokens.expiresIn * 1000));
  }
};

// Get token
export const getAccessToken = (): string | null => {
  if (typeof globalThis.window === 'undefined') return null;
  
  // Chekc if token is expired, if it is, logout user
  const expiry = localStorage.getItem('tokenExpiry');
  if (expiry && Date.now() > Number.parseInt(expiry)) {
    // Token expired
    logout();
    return null;
  }
  
  return localStorage.getItem('accessToken');
};

//Checks if they are logged in 
export const isAuthenticated = (): boolean => {
  if (typeof globalThis.window === 'undefined') return false;
  
  const token = getAccessToken();
  return !!token;
};

// Logout
//Do not need to call backend... we are not handling sessions
export const logout = (): void => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('idToken');
  localStorage.removeItem('tokenExpiry');
};