import { Redirect } from "expo-router"
import { useEffect, useState } from "react"
import { ActivityIndicator, View } from "react-native"
import { isLoggedIn } from "@/lib/auth"

export default function Index() {
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

  return <Redirect href={state === "in" ? "/(app)" : "/login"} />
}
