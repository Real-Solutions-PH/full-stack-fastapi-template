import { useAuthStore } from "@/stores/auth-store";
import { Redirect } from "expo-router";

export default function Index() {
	const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
	return <Redirect href={isAuthenticated ? "/(app)" : "/login"} />;
}
