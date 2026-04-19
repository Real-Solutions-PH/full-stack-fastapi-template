import { createMMKV } from "react-native-mmkv";
import type { StateStorage } from "zustand/middleware";

export const mmkv = createMMKV();

export const mmkvStorage: StateStorage = {
	getItem: (name) => mmkv.getString(name) ?? null,
	setItem: (name, value) => mmkv.set(name, value),
	removeItem: (name) => {
		mmkv.remove(name);
	},
};
