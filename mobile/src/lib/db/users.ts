export interface CachedUser {
	id: string;
	email: string;
	full_name: string | null;
	is_active: boolean;
	is_superuser: boolean;
	created_at?: string | null;
}

let cachedUser: CachedUser | null = {
	id: "demo-user",
	email: "ervinpiol7@gmail.com",
	full_name: "Ervin Piol",
	is_active: true,
	is_superuser: false,
	created_at: new Date().toISOString(),
};

export function getCachedUser(): CachedUser | null {
	return cachedUser;
}

export function upsertUser(user: CachedUser): void {
	cachedUser = { ...user };
}

export function clearUserCache(): void {
	cachedUser = null;
}
