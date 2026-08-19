const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FetchOptions {
	method?: 'GET' | 'POST' | 'DELETE' | 'PUT' | 'PATCH'
  	body?: unknown
}

export async function apiCall<T>(
	endpoint: string,
	options: FetchOptions = {}
): Promise<T> {
	const { method = 'GET', body } = options //  defaul method set to get

	const accessToken = localStorage.getItem("accessToken");

	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		'Authorization': 'Bearer ' + accessToken,
		// TODO: Remeber to come back and extract the actual auth token when zaman has set up the stuff
	}

	const response = await fetch(`${API_BASE}${endpoint}`,{
		method,
		headers,
		body: body ? JSON.stringify(body) : undefined,
	})

	if (!response.ok) {
		let errorMsg = `API call failed: ${response.statusText}`;

		try {
			const errorBody = await response.json();
			console.error("API error response:", errorBody);
			errorMsg = errorBody.detail || errorBody.message || errorMsg;
		} catch {
		}

		throw new Error(errorMsg);
	}

	if (response.status === 204) {
		return undefined as T;
	}

	return response.json() as Promise<T>;
}
