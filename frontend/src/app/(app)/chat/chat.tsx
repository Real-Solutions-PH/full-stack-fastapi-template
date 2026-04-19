"use client"

import { CopilotKit } from "@copilotkit/react-core"
import "@copilotkit/react-ui/styles.css"
import ChatPage from "@/components/Chat/ChatPage"
import { readAuthCookie } from "@/lib/auth"

export default function Chat() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? ""
  const runtimeUrl = `${apiUrl}/api/v1/copilotkit`

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Chat</h1>
        <p className="text-muted-foreground">Chat with AI agents</p>
      </div>
      <CopilotKit
        runtimeUrl={runtimeUrl}
        headers={{
          Authorization: `Bearer ${readAuthCookie() ?? ""}`,
        }}
      >
        <ChatPage />
      </CopilotKit>
    </div>
  )
}
