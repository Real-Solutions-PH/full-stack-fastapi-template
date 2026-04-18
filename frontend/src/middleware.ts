import { type NextRequest, NextResponse } from "next/server"

const AUTH_COOKIE = "access_token"

const publicRoutes = [
  "/landing",
  "/login",
  "/signup",
  "/recover-password",
  "/reset-password",
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get(AUTH_COOKIE)?.value
  const isPublic = publicRoutes.some((route) => pathname.startsWith(route))

  if (!token && !isPublic) {
    const url = request.nextUrl.clone()
    url.pathname = "/login"
    return NextResponse.redirect(url)
  }

  if (token && isPublic && pathname !== "/reset-password") {
    const url = request.nextUrl.clone()
    url.pathname = "/"
    return NextResponse.redirect(url)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|assets|favicon.ico).*)"],
}
