import { useNetworkStore } from "@/stores/network-store";
import { useEffect } from "react";

export function useNetworkStatus() {
	const setNetworkState = useNetworkStore((s) => s.setNetworkState);

	useEffect(() => {
		setNetworkState(true, "wifi");
	}, [setNetworkState]);
}
