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

OpenAPI.BASE = process.env.NEXT_PUBLIC_API_URL ?? ""
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
