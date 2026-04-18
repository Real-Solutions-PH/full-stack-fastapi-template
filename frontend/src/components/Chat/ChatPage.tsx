"use client"

import { CopilotChat } from "@copilotkit/react-ui"
import { Card, CardContent } from "@/components/ui/card"

export default function ChatPage() {
  return (
    <Card className="h-[calc(100vh-14rem)]">
      <CardContent className="h-full p-0 overflow-hidden">
        <CopilotChat
          labels={{
            title: "AI Assistant",
            initial: "Hi! How can I help you today?",
            placeholder: "Type a message...",
          }}
          className="h-full"
        />
      </CardContent>
    </Card>
  )
}
