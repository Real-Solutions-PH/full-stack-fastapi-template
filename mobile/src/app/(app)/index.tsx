import { useQuery } from "@tanstack/react-query"
import { ScrollView, View } from "react-native"
import { Text } from "@/components/ui/text"
import { api } from "@/lib/auth"
import type { CurrentUser } from "@/hooks/useAuth"

async function fetchMe(): Promise<CurrentUser> {
  const { data } = await api.get<CurrentUser>("/api/v1/users/me")
  return data
}

export default function HomeScreen() {
  const { data: user, isLoading } = useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchMe,
  })

  return (
    <ScrollView className="flex-1 bg-background">
      <View className="gap-4 p-6">
        <Text className="text-2xl font-bold">
          Hi{user?.full_name ? `, ${user.full_name}` : ""}
        </Text>
        {isLoading ? (
          <Text className="text-muted-foreground">Loading...</Text>
        ) : (
          <Text className="text-muted-foreground">{user?.email}</Text>
        )}
      </View>
    </ScrollView>
  )
}
