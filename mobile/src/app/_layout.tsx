import "../../global.css"
import { Stack } from "expo-router"
import { StatusBar } from "expo-status-bar"
import { Providers } from "@/components/providers"

export default function RootLayout() {
  return (
    <Providers>
      <StatusBar style="auto" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(app)" />
        <Stack.Screen name="login" />
        <Stack.Screen name="signup" />
        <Stack.Screen name="recover-password" />
        <Stack.Screen name="reset-password" />
      </Stack>
    </Providers>
  )
}
