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
import { clearAuthCookie, readAuthCookie } from "@/lib/auth"

OpenAPI.BASE = process.env.NEXT_PUBLIC_API_URL ?? ""
OpenAPI.TOKEN = async () => readAuthCookie() ?? ""

export function Providers({ children }: { children: ReactNode }) {
  const router = useRouter()

  const [queryClient] = useState(() => {
    const handleApiError = (error: Error) => {
      if (error instanceof ApiError && [401, 403].includes(error.status)) {
        clearAuthCookie()
        router.push("/login")
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
