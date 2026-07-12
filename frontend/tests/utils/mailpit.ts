import type { APIRequestContext } from "@playwright/test"

// The local Supabase stack (make supabase-up) ships Mailpit as its email
// testing server — web UI and API on http://127.0.0.1:54324.
const MAILPIT_HOST = process.env.MAILPIT_HOST ?? "http://127.0.0.1:54324"

type MailpitAddress = { Address: string; Name: string }

type MailpitMessageSummary = {
  ID: string
  To: MailpitAddress[]
  Subject: string
}

async function findMessageTo(
  request: APIRequestContext,
  email: string,
): Promise<MailpitMessageSummary | null> {
  const response = await request.get(`${MAILPIT_HOST}/api/v1/messages`)
  const data = (await response.json()) as {
    messages: MailpitMessageSummary[]
  }
  // Messages are returned newest first.
  return (
    data.messages.find((m) =>
      m.To.some((to) => to.Address.toLowerCase() === email.toLowerCase()),
    ) ?? null
  )
}

export async function findLastEmailTo({
  request,
  email,
  timeout = 10000,
}: {
  request: APIRequestContext
  email: string
  timeout?: number
}): Promise<MailpitMessageSummary> {
  const deadline = Date.now() + timeout
  while (Date.now() < deadline) {
    const message = await findMessageTo(request, email)
    if (message) return message
    await new Promise((resolve) => setTimeout(resolve, 200))
  }
  throw new Error(`Timeout while waiting for an email to ${email}`)
}

// Extracts the Supabase recovery link (/auth/v1/verify?...) from the most
// recent email sent to `email`.
export async function findRecoveryLink({
  request,
  email,
  timeout = 10000,
}: {
  request: APIRequestContext
  email: string
  timeout?: number
}): Promise<string> {
  const message = await findLastEmailTo({ request, email, timeout })
  const response = await request.get(
    `${MAILPIT_HOST}/api/v1/message/${message.ID}`,
  )
  const body = (await response.json()) as { HTML: string; Text: string }
  const content = `${body.Text ?? ""}\n${body.HTML ?? ""}`
  const match = content.match(
    /https?:\/\/[^\s"'<>]*\/auth\/v1\/verify[^\s"'<>]*/,
  )
  if (!match) {
    throw new Error(`No recovery link found in the email to ${email}`)
  }
  // The link may come from the HTML part with encoded ampersands.
  return match[0].replace(/&amp;/g, "&")
}
