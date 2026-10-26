import { getApiBaseUrl } from '@/lib/api/auth';

export const AUTH_EVENT = 'watchdog-auth-changed';
import { storeAccessToken, readAccessToken, clearAccessToken } from './token_store';



export const clearLegacyProfileStorage = () => {
  if (typeof window === "undefined") return;

  for (const key of ["userSub", "fullname", "email", "address"]) {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  }

  // Remove old offline caches that contained property addresses.
  for (let index = localStorage.length - 1; index >= 0; index--) {
    const key = localStorage.key(index);

    if (
      key?.startsWith("watchdog:critical-alert-map:") &&
      !key.startsWith("watchdog:critical-alert-map:v2:")
    ) {
      localStorage.removeItem(key);
    }
  }
};


// Types for API responses
interface SignUpResponse {
  success: boolean,
  data: {
    user_sub: string;
    user_confirmed: boolean;
  };
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
  success: boolean,
  data: {
    confirmed: boolean;
  };
}

interface VerifyMfaResponse {
  success: boolean;
  data: {
    access_token: string;
    id_token: string;
    token_type?: string | null;
    expires_in?: number;
  };
}

interface RefreshResponse {
  success: boolean;
  data: {
  access_token: string;
  id_token: string;
  expires_in?: number;
  token_type?: string | null;
};
}

let refreshPromise: Promise<string> | null = null;




// API Client with error handling
const apiClient = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
    ...options,
    credentials: "include",
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
      userSub: response.data.user_sub,
      confirmed: response.data.user_confirmed,
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

    return response.data.confirmed;
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



  storeAccessToken(tokens.accessToken, tokens.expiresIn ?? 3600);

  clearLegacyProfileStorage();


  window.dispatchEvent(new Event(AUTH_EVENT));
  
};


// Get token
export const getAccessToken = (): string | null => {
  return readAccessToken();
  };

//Checks if they are logged in 
export const isAuthenticated = (): boolean => {
  return readAccessToken() !== null;
};





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

export const refreshSession = async (): Promise<string> => {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const response = await apiClient<RefreshResponse>("/auth/refresh", {
      method: "POST",
    });

    setSession({
      accessToken: response.data.access_token,
      idToken: response.data.id_token,
      expiresIn: response.data.expires_in,
    });

    return response.data.access_token;
  })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
};


export const clearSession = (): void => {
  clearAccessToken();

  if (typeof window !== "undefined") {
    clearLegacyProfileStorage();
    window.dispatchEvent(new Event(AUTH_EVENT));
  }
};

export const logout = async (): Promise<void> => {
  try {
    await fetch(`${getApiBaseUrl()}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } finally {
    clearSession();
  }
};
