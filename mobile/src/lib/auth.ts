export const API_URL = "";

interface FakeResponse<T> {
	data: T;
	status: number;
}

async function fakeRequest<T>(): Promise<FakeResponse<T>> {
	return { data: {} as T, status: 200 };
}

export const api = {
	get: <T>(_url: string, _config?: unknown) => fakeRequest<T>(),
	post: <T>(_url: string, _body?: unknown, _config?: unknown) => fakeRequest<T>(),
	put: <T>(_url: string, _body?: unknown, _config?: unknown) => fakeRequest<T>(),
	delete: <T>(_url: string, _config?: unknown) => fakeRequest<T>(),
	patch: <T>(_url: string, _body?: unknown, _config?: unknown) => fakeRequest<T>(),
};

export async function getAccessToken(): Promise<string | null> {
	return null;
}

export async function setAccessToken(_token: string): Promise<void> {}

export async function clearAccessToken(): Promise<void> {}

export async function isLoggedIn(): Promise<boolean> {
	return true;
}

export function createApiClient() {
	return api;
}
