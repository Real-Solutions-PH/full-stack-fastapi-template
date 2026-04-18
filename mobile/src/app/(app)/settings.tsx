import { View } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { Button } from "@/components/ui/button"
import { Text } from "@/components/ui/text"
import { useAuth } from "@/hooks/useAuth"

export default function SettingsScreen() {
  const { logout, user } = useAuth()
  return (
    <SafeAreaView className="flex-1 bg-background">
      <View className="flex-1 gap-6 p-6">
        <Text className="text-2xl font-bold">Settings</Text>
        {user ? (
          <View className="gap-1">
            <Text className="text-sm text-muted-foreground">Signed in as</Text>
            <Text className="font-medium">{user.email}</Text>
          </View>
        ) : null}
        <Button variant="destructive" label="Log out" onPress={logout} />
      </View>
    </SafeAreaView>
  )
}
