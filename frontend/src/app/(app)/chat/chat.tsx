"use client"

import { CopilotKit } from "@copilotkit/react-core"
import "@copilotkit/react-ui/styles.css"
import { useEffect, useState } from "react"
import ChatPage from "@/components/Chat/ChatPage"
import { createClient } from "@/lib/supabase/client"

export default function Chat() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? ""
  const runtimeUrl = `${apiUrl}/api/v1/copilotkit`
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    createClient()
      .auth.getSession()
      .then(({ data }) => {
        setToken(data.session?.access_token ?? "")
      })
  }, [])

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Chat</h1>
        <p className="text-muted-foreground">Chat with AI agents</p>
      </div>
      {token !== null && (
        <CopilotKit
          runtimeUrl={runtimeUrl}
          headers={{
            Authorization: `Bearer ${token}`,
          }}
        >
          <ChatPage />
        </CopilotKit>
      )}
    </div>
  )
}
