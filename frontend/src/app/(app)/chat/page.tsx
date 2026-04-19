import type { Metadata } from "next"
import Chat from "./chat"

export const metadata: Metadata = {
  title: "Chat - FastAPI Template",
}

export default function Page() {
  return <Chat />
}
