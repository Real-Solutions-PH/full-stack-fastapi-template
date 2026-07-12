import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"

// Server Components / Route Handlers Supabase client (canonical @supabase/ssr
// pattern). Create a new client per request — never share it across requests.
export async function createClient() {
  const cookieStore = await cookies()

  // SUPABASE_URL overrides for server-side reachability (see middleware.ts).
  return createServerClient(
    process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            for (const { name, value, options } of cookiesToSet) {
              cookieStore.set(name, value, options)
            }
          } catch {
            // Called from a Server Component — cookie writes are not allowed
            // there. Safe to ignore when the middleware refreshes sessions.
          }
        },
      },
    },
  )
}
