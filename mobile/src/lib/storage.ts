import { Platform } from "react-native";
import type { StateStorage } from "zustand/middleware";

interface KVStore {
	getString(key: string): string | undefined;
	set(key: string, value: string): void;
	remove(key: string): void;
}

function createWebStore(): KVStore {
	const memory = new Map<string, string>();
	const hasLocalStorage =
		globalThis.window !== undefined && !!globalThis.localStorage;

	return {
		getString(key) {
			if (hasLocalStorage) {
				return globalThis.localStorage.getItem(key) ?? undefined;
			}
			return memory.get(key);
		},
		set(key, value) {
			if (hasLocalStorage) {
				globalThis.localStorage.setItem(key, value);
				return;
			}
			memory.set(key, value);
		},
		remove(key) {
			if (hasLocalStorage) {
				globalThis.localStorage.removeItem(key);
				return;
			}
			memory.delete(key);
		},
	};
}

function createNativeStore(): KVStore {
	const { createMMKV } =
		require("react-native-mmkv") as typeof import("react-native-mmkv");
	const instance = createMMKV();
	return {
		getString: (key) => instance.getString(key),
		set: (key, value) => instance.set(key, value),
		remove: (key) => instance.remove(key),
	};
}

export const mmkv: KVStore =
	Platform.OS === "web" ? createWebStore() : createNativeStore();

export const mmkvStorage: StateStorage = {
	getItem: (name) => mmkv.getString(name) ?? null,
	setItem: (name, value) => mmkv.set(name, value),
	removeItem: (name) => {
		mmkv.remove(name);
	},
};
