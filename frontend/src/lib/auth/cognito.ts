const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types for API responses
interface SignUpResponse {
  user_sub: string;
  confirmed: boolean;
}

interface LoginResponse {
  access_token: string;
  id_token: string;
  expires_in: number;
}

interface ConfirmResponse {
  confirmed: boolean;
  result: any;
}

// API Client with error handling
const apiClient = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
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
  name: string,
  address: string
): Promise<{ userSub: string; confirmed: boolean }> => {//expects to return these back
  try {
    const response = await apiClient<SignUpResponse>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, name, address }),//create JSON for API Post
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

    return {
      accessToken: response.access_token,
      idToken: response.id_token,
      expiresIn: response.expires_in,
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

// ✅ Store tokens (same as before)
export const setSession = (tokens: { 
  accessToken: string; 
  idToken: string;
  expiresIn?: number;
}) => {
  localStorage.setItem('accessToken', tokens.accessToken);
  localStorage.setItem('idToken', tokens.idToken);
};

// ✅ Get token (same as before)
export const getAccessToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  // Chekc if token is expired, if it is, logout user
  const expiry = localStorage.getItem('tokenExpiry');
  if (expiry && Date.now() > parseInt(expiry)) {
    // Token expired
    logout();
    return null;
  }
  
  return localStorage.getItem('accessToken');
};

//Checks if they are logged in 
export const isAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;
  
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