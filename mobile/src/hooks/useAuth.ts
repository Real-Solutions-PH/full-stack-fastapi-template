import { useCustomToast } from "@/hooks/useCustomToast";
import { api, clearAccessToken, setAccessToken } from "@/lib/auth";
import * as itemsDb from "@/lib/db/items";
import * as syncQueueDb from "@/lib/db/sync-queue";
import * as usersDb from "@/lib/db/users";
import { runSync } from "@/lib/sync";
import { handleError } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useMutation, useQueryClient } from "@tanstack/react-query";
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

async function loginRequest(
	input: LoginInput,
): Promise<{ access_token: string }> {
	const body = new URLSearchParams();
	body.append("username", input.username);
	body.append("password", input.password);
	const { data } = await api.post<{ access_token: string }>(
		"/api/v1/login/access-token",
		body.toString(),
		{ headers: { "Content-Type": "application/x-www-form-urlencoded" } },
	);
	return data;
}

async function signupRequest(input: SignupInput): Promise<CurrentUser> {
	const { data } = await api.post<CurrentUser>("/api/v1/users/signup", input);
	return data;
}

export function useAuth() {
	const queryClient = useQueryClient();
	const router = useRouter();
	const toast = useCustomToast();
	const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

	const login = useMutation({
		mutationFn: loginRequest,
		onSuccess: async (data) => {
			await setAccessToken(data.access_token);

			try {
				const { data: user } = await api.get<CurrentUser>("/api/v1/users/me");
				usersDb.upsertUser({
					id: user.id,
					email: user.email,
					full_name: user.full_name ?? null,
					is_active: user.is_active,
					is_superuser: user.is_superuser,
				});
				useAuthStore.getState().setAuthenticated(user);
				runSync();
			} catch {
				// Offline login — mark authenticated anyway (token stored)
				useAuthStore.getState().setAuthenticated({
					id: "",
					email: "",
				});
			}

			router.replace("/(app)");
		},
		onError: (err) => toast.error(handleError(err)),
	});

	const signup = useMutation({
		mutationFn: signupRequest,
		onSuccess: () => {
			toast.success("Account created. Please log in.");
			router.replace("/login");
		},
		onError: (err) => toast.error(handleError(err)),
	});

	async function logout() {
		await clearAccessToken();
		useAuthStore.getState().clearAuth();
		usersDb.clearUserCache();
		itemsDb.clearItems();
		syncQueueDb.clearSyncQueue();
		queryClient.removeQueries();
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
