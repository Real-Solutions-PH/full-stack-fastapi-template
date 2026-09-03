import {
  createClient,
  type SupabaseClient,
  type SupportedStorage,
} from "@supabase/supabase-js"
import { AppState, Platform } from "react-native"
import { mmkv } from "@/lib/storage"

// GoTrue session storage backed by the app's existing MMKV util (which
// already falls back to localStorage / in-memory on web with SSR guards).
const sessionStorage: SupportedStorage = {
  getItem: (key) => mmkv.getString(key) ?? null,
  setItem: (key, value) => {
    mmkv.set(key, value)
  },
  removeItem: (key) => {
    mmkv.remove(key)
  },
}

let client: SupabaseClient | null = null

function createSupabaseClient(): SupabaseClient {
  const url =
    process.env.EXPO_PUBLIC_SUPABASE_URL ??
    (__DEV__ ? "http://127.0.0.1:54321" : undefined)
  const anonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY

  if (!url || !anonKey) {
    throw new Error(
      "Supabase is not configured. Set EXPO_PUBLIC_SUPABASE_URL and " +
        "EXPO_PUBLIC_SUPABASE_ANON_KEY (see mobile/.env.example).",
    )
  }

  const instance = createClient(url, anonKey, {
    auth: {
      storage: sessionStorage,
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,
    },
  })

  // On native there are no browser visibility events, so drive GoTrue's
  // token auto-refresh timer from the app foreground state instead.
  if (Platform.OS !== "web") {
    AppState.addEventListener("change", (state) => {
      if (state === "active") {
        instance.auth.startAutoRefresh()
      } else {
        instance.auth.stopAutoRefresh()
      }
    })
    instance.auth.startAutoRefresh()
  }

  return instance
}

/**
 * Lazily-initialized Supabase client. Initialization is deferred to first
 * use so that importing this module never throws (keeps static web export
 * working when EXPO_PUBLIC_SUPABASE_* is unset).
 */
export function getSupabase(): SupabaseClient {
  client ??= createSupabaseClient()
  return client
}
