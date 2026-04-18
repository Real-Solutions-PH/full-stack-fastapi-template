import { Redirect, Tabs } from "expo-router"
import { useEffect, useState } from "react"
import { ActivityIndicator, View } from "react-native"
import { isLoggedIn } from "@/lib/auth"

export default function AppLayout() {
  const [state, setState] = useState<"loading" | "in" | "out">("loading")

  useEffect(() => {
    isLoggedIn().then((logged) => setState(logged ? "in" : "out"))
  }, [])

  if (state === "loading") {
    return (
      <View className="flex-1 items-center justify-center bg-background">
        <ActivityIndicator />
      </View>
    )
  }

  if (state === "out") return <Redirect href="/login" />

  return (
    <Tabs screenOptions={{ headerShown: true }}>
      <Tabs.Screen name="index" options={{ title: "Home" }} />
      <Tabs.Screen name="items" options={{ title: "Items" }} />
      <Tabs.Screen name="settings" options={{ title: "Settings" }} />
    </Tabs>
  )
}
