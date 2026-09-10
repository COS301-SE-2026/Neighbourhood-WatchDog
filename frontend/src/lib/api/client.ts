import { getAccessToken, refreshSession, clearSession } from "@/lib/auth/cognito"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FetchOptions {
	method?: 'GET' | 'POST' | 'DELETE' | 'PUT' | 'PATCH'
  	body?: unknown
}

async function sendRequest(
	endpoint: string,
	options: FetchOptions,
	token: string
): Promise<Response> {
	const { method = "GET", body} = options;

	return fetch(`${API_BASE}${endpoint}`, {
		method,
		credentials: "include",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`
		},
		body: body === undefined ? undefined : JSON.stringify(body)
	});
}

export async function apiCall<T>(
	endpoint: string,
	options: FetchOptions = {}
): Promise<T> {

	let token = getAccessToken()

	if (!token) {
		try {
			token = await refreshSession();
		} catch {
			clearSession();
			throw new Error("Your session has expired. Please log in again.")
		}
	}

	let response = await sendRequest(endpoint, options, token);

	if (response.status === 401) {

		try {
			token = await refreshSession();
			response = await sendRequest(endpoint, options, token);
		} catch {
			clearSession();
			throw new Error("Your session has expired. Please log in again.");
		}
	}

	if (!response.ok) {
		let errorMessage = `API call failed: ${response.statusText}`
		try {
			const errorBody = await response.json();
			errorMessage = 
				errorBody.detail?.message ||
				errorBody.detail ||
				errorBody.message ||
				errorMessage;
		} catch {
		
		}

		throw new Error(errorMessage);
	}
	

	if (response.status === 204) {
		return undefined as T;
	}

	return response.json() as Promise<T>;
}
