export const AUTH_COOKIE = "access_token"

export function setAuthCookie(token: string, maxAgeSeconds = 60 * 60 * 24 * 7) {
  if (typeof document === "undefined") return
  const secure = window.location.protocol === "https:" ? "; Secure" : ""
  document.cookie = `${AUTH_COOKIE}=${token}; Path=/; Max-Age=${maxAgeSeconds}; SameSite=Lax${secure}`
}

export function clearAuthCookie() {
  if (typeof document === "undefined") return
  document.cookie = `${AUTH_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`
}

export function readAuthCookie(): string | null {
  if (typeof document === "undefined") return null
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${AUTH_COOKIE}=`))
  return match ? decodeURIComponent(match.split("=")[1]) : null
}

export function isLoggedIn(): boolean {
  return readAuthCookie() !== null
}
