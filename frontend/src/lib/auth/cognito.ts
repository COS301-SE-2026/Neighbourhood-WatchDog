import { getApiBaseUrl } from '@/lib/api/auth';
import { jwtDecode } from 'jwt-decode';

export const AUTH_EVENT = 'watchdog-auth-changed';

// Types for API responses
interface SignUpResponse {
  user_sub: string;
  confirmed: boolean;
}

interface LoginResponse {
  success: boolean;
  data: {
    mfa_required?: boolean;

    session?: string;

    delivery?: {
      medium: string;
      destination: string;
    };

    access_token?: string;
    id_token?: string;
    refresh_token?: string | null;
    token_type?: string | null;
    expires_in?: number;
  };
}

interface LoginResult {
  mfaRequired: boolean;

  session?: string;

  delivery?: {
    medium: string;
    destination: string;
  };

  accessToken?: string;
  idToken?: string;
  expiresIn?: number;
}

interface ConfirmResponse {
  confirmed: boolean;
}

interface VerifyMfaResponse {
  success: boolean;
  data: {
    access_token: string;
    id_token: string;
    refresh_token?: string | null;
    token_type?: string | null;
    expires_in?: number;
  };
}

export interface StoredUser {
  sub: string;
  fullname: string;
  email: string;
  address: string;
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
): Promise<LoginResult> => {
  try {
    const response = await apiClient<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    const data = response.data;

    // MFA required
    if (data.mfa_required) {
      return {
        mfaRequired: true,
        session: data.session,
        delivery: data.delivery,
      };
    }

    // Login complete
    return {
      mfaRequired: false,
      accessToken: data.access_token,
      idToken: data.id_token,
      expiresIn: data.expires_in ?? 0,
    };
  } catch (error) {
    console.error("Login error:", error);
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
  if (typeof window === 'undefined') return;

  if (!tokens.accessToken || !tokens.idToken) {
    throw new Error('Cannot store empty auth tokens');
  }

  const claims = jwtDecode<{
    sub: string;
    name?: string;
    email?: string;
    address?: { formatted?: string };
  }>(tokens.idToken);

  localStorage.setItem('accessToken', tokens.accessToken);
  localStorage.setItem('idToken', tokens.idToken);
  localStorage.setItem('userSub', claims.sub);
  localStorage.setItem('fullname', claims.name ?? '');
  localStorage.setItem('email', claims.email ?? '');
  localStorage.setItem('address', claims.address?.formatted ?? '');

  if (typeof tokens.expiresIn === 'number') {
    localStorage.setItem('tokenExpiry', String(Date.now() + tokens.expiresIn * 1000));
  }

  window.dispatchEvent(new Event(AUTH_EVENT));
  
};

export const updateStoredFullName = (fullname: string) => {
  if (typeof window === "undefined") return;

  localStorage.setItem("fullname", fullname);
  window.dispatchEvent(new Event(AUTH_EVENT));
}
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
  if (typeof window === 'undefined') return;
  
  localStorage.removeItem('accessToken');
  localStorage.removeItem('idToken');
  localStorage.removeItem('tokenExpiry');
};

export const getStoredUser = (): StoredUser | null => {
  if (typeof window === 'undefined') return null;
  if (!isAuthenticated()) return null;

  const sub = localStorage.getItem('userSub');
  if (!sub) return null;

  return {
    sub,
    fullname: localStorage.getItem('fullname') ?? '',
    email: localStorage.getItem('email') ?? '',
    address: localStorage.getItem('address') ?? '',
  }
}

export const verifyMfa = async (
  email: string,
  session: string,
  code: string
): Promise<{
  accessToken: string;
  idToken: string;
  expiresIn: number;
}> => {
  const response = await apiClient<VerifyMfaResponse>("/auth/verify-mfa", {
    method: "POST",
    body: JSON.stringify({
      email,
      session,
      code,
    }),
  });

  return {
    accessToken: response.data.access_token,
    idToken: response.data.id_token,
    expiresIn: response.data.expires_in ?? 0,
  };
};