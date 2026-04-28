import { useCustomToast } from "@/hooks/useCustomToast";
import * as usersDb from "@/lib/db/users";
import { useAuthStore } from "@/stores/auth-store";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";

export interface CurrentUser {
	id: string;
	email: string;
	is_active: boolean;
	is_superuser: boolean;
	full_name?: string | null;
}

interface LoginInput {
	username: string;
	password: string;
}

interface SignupInput {
	email: string;
	password: string;
	full_name?: string;
}

export function useAuth() {
	const router = useRouter();
	const toast = useCustomToast();
	const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

	const login = useMutation({
		mutationFn: async (_input: LoginInput) => undefined,
		onSuccess: () => {
			useAuthStore.getState().setAuthenticated({
				id: "demo-user",
				email: "ervinpiol7@gmail.com",
				full_name: "Ervin Piol",
			});
			router.replace("/(app)");
		},
	});

	const signup = useMutation({
		mutationFn: async (_input: SignupInput) => undefined,
		onSuccess: () => {
			toast.success("Account created. Please log in.");
			router.replace("/login");
		},
	});

	async function logout() {
		useAuthStore.getState().clearAuth();
		router.replace("/login");
	}

	const user = usersDb.getCachedUser();

	return {
		user,
		isAuthenticated,
		login,
		signup,
		logout,
	};
}
