import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";
import * as recipesDb from "@/lib/db/recipes";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, Pressable, ScrollView, View } from "react-native";

export default function RecipeDetailScreen() {
	const { id } = useLocalSearchParams<{ id: string }>();
	const router = useRouter();
	const [version, setVersion] = useState(0);

	useFocusEffect(
		useCallback(() => {
			setVersion((v) => v + 1);
		}, []),
	);

	const recipe = recipesDb.getRecipeById(id);
	const items = recipe ? recipesDb.getRecipeItems(id) : [];
	void version;

	if (!recipe) {
		return (
			<View className="flex-1 items-center justify-center bg-background p-6">
				<Text>Recipe not found</Text>
				<Button
					label="Back"
					variant="outline"
					className="mt-4"
					onPress={() => router.back()}
				/>
			</View>
		);
	}

	const check = recipesDb.preCookCheck(id, 1);

	const handleDelete = () => {
		Alert.alert("Delete recipe", `Delete "${recipe.name}"?`, [
			{ text: "Cancel", style: "cancel" },
			{
				text: "Delete",
				style: "destructive",
				onPress: () => {
					recipesDb.deleteRecipe(recipe.id);
					router.back();
				},
			},
		]);
	};

	return (
		<ScrollView
			className="flex-1 bg-background"
			contentContainerClassName="p-4 gap-4"
		>
			<View>
				<Text className="text-2xl font-bold">{recipe.name}</Text>
				{recipe.yield_qty ? (
					<Text className="text-sm text-muted-foreground">
						Yields {recipe.yield_qty} {recipe.yield_unit ?? ""}
					</Text>
				) : null}
			</View>

			{recipe.notes ? (
				<View className="rounded-lg border border-border p-3">
					<Text className="text-xs text-muted-foreground">Notes</Text>
					<Text className="mt-1 text-sm">{recipe.notes}</Text>
				</View>
			) : null}

			<View>
				<Text className="mb-2 text-lg font-semibold">Ingredients</Text>
				{items.length === 0 ? (
					<Text className="text-sm text-muted-foreground">No ingredients</Text>
				) : (
					<View className="rounded-lg border border-border">
						{items.map((it, idx) => {
							const row = check.items.find(
								(c) => c.product_id === it.product_id,
							);
							const short = row && row.short > 0;
							return (
								<View
									key={it.product_id}
									className={`flex-row items-center justify-between p-3 ${
										idx > 0 ? "border-t border-border" : ""
									}`}
								>
									<View className="flex-1">
										<Text className="font-medium">{it.product_name}</Text>
										<Text
											className={`text-xs ${
												short ? "text-destructive" : "text-muted-foreground"
											}`}
										>
											Need {it.quantity} {it.product_unit} · have{" "}
											{it.current_stock} {it.product_unit}
											{short ? ` · short ${row?.short}` : ""}
										</Text>
									</View>
								</View>
							);
						})}
					</View>
				)}
			</View>

			<View className="flex-row gap-2">
				<Button
					label="Batch cook"
					className="flex-1"
					onPress={() => router.push(`/recipes/${recipe.id}/cook`)}
					disabled={items.length === 0}
				/>
				<Button
					label="Edit"
					variant="outline"
					className="flex-1"
					onPress={() => router.push(`/recipes/${recipe.id}/edit`)}
				/>
			</View>

			<Pressable onPress={handleDelete} className="items-center py-2">
				<Text className="text-sm text-destructive">Delete recipe</Text>
			</Pressable>
		</ScrollView>
	);
}
