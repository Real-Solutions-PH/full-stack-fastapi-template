import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";
import * as recipesDb from "@/lib/db/recipes";
import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { FlatList, Pressable, View } from "react-native";

export default function RecipesIndexScreen() {
	const router = useRouter();
	const [version, setVersion] = useState(0);

	useFocusEffect(
		useCallback(() => {
			setVersion((v) => v + 1);
		}, []),
	);

	void version;
	const recipes = recipesDb.listRecipes();

	return (
		<View className="flex-1 bg-background p-4">
			<View className="mb-3 flex-row items-center justify-between">
				<Text className="text-sm text-muted-foreground">
					{recipes.length} recipe{recipes.length === 1 ? "" : "s"}
				</Text>
				<Button
					label="New recipe"
					onPress={() => router.push("/recipes/new")}
				/>
			</View>

			<FlatList
				data={recipes}
				keyExtractor={(r) => r.id}
				ItemSeparatorComponent={() => <View className="h-px bg-border" />}
				ListEmptyComponent={
					<View className="items-center py-10">
						<Text className="text-muted-foreground">No recipes yet</Text>
						<Text className="mt-1 text-xs text-muted-foreground">
							Create one to enable batch cook mode
						</Text>
					</View>
				}
				renderItem={({ item }) => (
					<Pressable
						onPress={() => router.push(`/recipes/${item.id}`)}
						className="flex-row items-center justify-between py-3 active:opacity-60"
					>
						<View className="flex-1">
							<Text className="font-medium">{item.name}</Text>
							<Text className="text-xs text-muted-foreground">
								{item.item_count} ingredient{item.item_count === 1 ? "" : "s"}
								{item.yield_qty
									? ` · yields ${item.yield_qty} ${item.yield_unit ?? ""}`
									: ""}
							</Text>
						</View>
						<Text className="text-muted-foreground">›</Text>
					</Pressable>
				)}
			/>
		</View>
	);
}
