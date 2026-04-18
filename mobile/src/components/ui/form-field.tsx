import type { ReactNode } from "react"
import { View } from "react-native"
import { Text } from "@/components/ui/text"

interface FormFieldProps {
  label?: string
  error?: string
  children: ReactNode
}

export function FormField({ label, error, children }: FormFieldProps) {
  return (
    <View className="gap-1.5">
      {label ? (
        <Text className="text-sm font-medium text-foreground">{label}</Text>
      ) : null}
      {children}
      {error ? (
        <Text className="text-xs text-destructive">{error}</Text>
      ) : null}
    </View>
  )
}
