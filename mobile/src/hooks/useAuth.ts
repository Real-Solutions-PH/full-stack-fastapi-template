import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "expo-router"
import {
  api,
  clearAccessToken,
  isLoggedIn,
  setAccessToken,
} from "@/lib/auth"
import { handleError } from "@/lib/utils"
import { useCustomToast } from "@/hooks/useCustomToast"

export interface CurrentUser {
  id: string
  email: string
  is_active: boolean
  is_superuser: boolean
  full_name?: string | null
}

interface LoginInput {
  username: string
  password: string
}

interface SignupInput {
  email: string
  password: string
  full_name?: string
}

async function fetchMe(): Promise<CurrentUser> {
  const { data } = await api.get<CurrentUser>("/api/v1/users/me")
  return data
}

async function loginRequest(input: LoginInput): Promise<{ access_token: string }> {
  const body = new URLSearchParams()
  body.append("username", input.username)
  body.append("password", input.password)
  const { data } = await api.post<{ access_token: string }>(
    "/api/v1/login/access-token",
    body.toString(),
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } },
  )
  return data
}

async function signupRequest(input: SignupInput): Promise<CurrentUser> {
  const { data } = await api.post<CurrentUser>("/api/v1/users/signup", input)
  return data
}

export function useAuth() {
  const queryClient = useQueryClient()
  const router = useRouter()
  const toast = useCustomToast()

  const userQuery = useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchMe,
    retry: false,
    enabled: false,
  })

  const login = useMutation({
    mutationFn: loginRequest,
    onSuccess: async (data) => {
      await setAccessToken(data.access_token)
      await queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      router.replace("/(app)")
    },
    onError: (err) => toast.error(handleError(err)),
  })

  const signup = useMutation({
    mutationFn: signupRequest,
    onSuccess: () => {
      toast.success("Account created. Please log in.")
      router.replace("/login")
    },
    onError: (err) => toast.error(handleError(err)),
  })

  async function logout() {
    await clearAccessToken()
    queryClient.removeQueries({ queryKey: ["currentUser"] })
    router.replace("/login")
  }

  return {
    user: userQuery.data,
    isLoadingUser: userQuery.isLoading,
    login,
    signup,
    logout,
    isLoggedIn,
  }
}
