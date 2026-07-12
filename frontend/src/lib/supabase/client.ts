import { createBrowserClient } from "@supabase/ssr"

import { AUTH_COOKIE_OPTIONS } from "@/lib/supabase/cookie"

// Returns the shared browser Supabase client (createBrowserClient returns a
// singleton). Sessions are stored in cookies so the Next.js middleware can
// read and refresh them.
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
    { cookieOptions: AUTH_COOKIE_OPTIONS },
  )
}
