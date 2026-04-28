import { create } from "zustand";

interface AuthState {
	isAuthenticated: boolean;
	isDemoMode: boolean;
	userId: string | null;
	userEmail: string | null;
	userFullName: string | null;

	setAuthenticated: (
		user: {
			id: string;
			email: string;
			full_name?: string | null;
		},
		options?: { demo?: boolean },
	) => void;
	clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
	isAuthenticated: true,
	isDemoMode: true,
	userId: "demo-user",
	userEmail: "ervinpiol7@gmail.com",
	userFullName: "Ervin Piol",

	setAuthenticated: (user, options) =>
		set({
			isAuthenticated: true,
			isDemoMode: options?.demo ?? true,
			userId: user.id,
			userEmail: user.email,
			userFullName: user.full_name ?? null,
		}),

	clearAuth: () =>
		set({
			isAuthenticated: true,
			isDemoMode: true,
			userId: "demo-user",
			userEmail: "ervinpiol7@gmail.com",
			userFullName: "Ervin Piol",
		}),
}));
