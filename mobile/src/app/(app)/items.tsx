import { useQuery } from "@tanstack/react-query"
import { FlatList, View } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { Text } from "@/components/ui/text"
import { api } from "@/lib/auth"

interface Item {
  id: string
  title: string
  description?: string | null
}

interface ItemsResponse {
  data: Item[]
  count: number
}

async function fetchItems(): Promise<ItemsResponse> {
  const { data } = await api.get<ItemsResponse>("/api/v1/items/")
  return data
}

export default function ItemsScreen() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["items"],
    queryFn: fetchItems,
  })

  return (
    <SafeAreaView className="flex-1 bg-background">
      <View className="flex-1 p-4">
        <Text className="mb-4 text-2xl font-bold">Items</Text>
        {isLoading ? (
          <Text className="text-muted-foreground">Loading...</Text>
        ) : error ? (
          <Text className="text-destructive">Failed to load items</Text>
        ) : (
          <FlatList
            data={data?.data ?? []}
            keyExtractor={(it) => it.id}
            ItemSeparatorComponent={() => <View className="h-px bg-border" />}
            ListEmptyComponent={
              <Text className="text-muted-foreground">No items yet</Text>
            }
            renderItem={({ item }) => (
              <View className="py-3">
                <Text className="font-medium">{item.title}</Text>
                {item.description ? (
                  <Text className="text-sm text-muted-foreground">
                    {item.description}
                  </Text>
                ) : null}
              </View>
            )}
          />
        )}
      </View>
    </SafeAreaView>
  )
}
