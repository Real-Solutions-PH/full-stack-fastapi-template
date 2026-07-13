"use client"

import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { useRouter } from "next/navigation"
import { type ReactNode, useState } from "react"
import { ApiError, OpenAPI } from "@/client"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/sonner"
import { createClient } from "@/lib/supabase/client"

// NEXT_PUBLIC_API_URL is the BROWSER-facing backend URL. When the frontend
// runs in a container (compose/CI), that URL — http://localhost:8000 — points
// at the frontend container itself during SSR, and every server-side render
// of a useSuspenseQuery page died with ECONNREFUSED. API_URL overrides the
// base for the server runtime only (http://backend:8000 on the compose
// network); it is not a NEXT_PUBLIC_ var, so it is never inlined into the
// browser bundle and the client always uses NEXT_PUBLIC_API_URL.
OpenAPI.BASE =
  (typeof window === "undefined" ? process.env.API_URL : undefined) ??
  process.env.NEXT_PUBLIC_API_URL ??
  ""
OpenAPI.TOKEN = async () => {
  // Guard SSR: the browser Supabase client needs window/document cookies.
  if (typeof window === "undefined") return ""
  const { data } = await createClient().auth.getSession()
  return data.session?.access_token ?? ""
}

export function Providers({ children }: { children: ReactNode }) {
  const router = useRouter()

  const [queryClient] = useState(() => {
    const handleApiError = (error: Error) => {
      // SSR renders can surface 401s too; sign-out is browser-only (the old
      // cookie helpers had the same typeof-document guard).
      if (typeof window === "undefined") return
      if (error instanceof ApiError && [401, 403].includes(error.status)) {
        createClient()
          .auth.signOut({ scope: "local" })
          .finally(() => {
            router.push("/login")
            router.refresh()
          })
      }
    }
    return new QueryClient({
      queryCache: new QueryCache({ onError: handleApiError }),
      mutationCache: new MutationCache({ onError: handleApiError }),
    })
  })

  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange
    >
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster richColors closeButton />
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ThemeProvider>
  )
}
