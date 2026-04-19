import { runSync } from "@/lib/sync";
import { useEffect, useRef } from "react";
import { AppState } from "react-native";

export function useSyncOnForeground() {
	const appState = useRef(AppState.currentState);

	useEffect(() => {
		const sub = AppState.addEventListener("change", (nextState) => {
			if (
				appState.current.match(/inactive|background/) &&
				nextState === "active"
			) {
				runSync();
			}
			appState.current = nextState;
		});

		return () => sub.remove();
	}, []);
}
