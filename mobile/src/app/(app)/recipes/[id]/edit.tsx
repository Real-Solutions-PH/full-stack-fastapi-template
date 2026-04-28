import { RecipeForm } from "@/components/recipe-form";
import { Text } from "@/components/ui/text";
import * as recipesDb from "@/lib/db/recipes";
import { useLocalSearchParams, useRouter } from "expo-router";
import { View } from "react-native";

export default function EditRecipeScreen() {
	const { id } = useLocalSearchParams<{ id: string }>();
	const router = useRouter();
	const recipe = recipesDb.getRecipeById(id);
	const items = recipe ? recipesDb.getRecipeItems(id) : [];

	if (!recipe) {
		return (
			<View className="flex-1 items-center justify-center bg-background">
				<Text>Recipe not found</Text>
			</View>
		);
	}

	return (
		<RecipeForm
			initial={{
				name: recipe.name,
				yield_qty: recipe.yield_qty,
				yield_unit: recipe.yield_unit,
				notes: recipe.notes,
				items: items.map((i) => ({
					product_id: i.product_id,
					quantity: i.quantity,
				})),
			}}
			submitLabel="Save changes"
			onCancel={() => router.back()}
			onSubmit={(value) => {
				recipesDb.updateRecipe(recipe.id, {
					name: value.name,
					yield_qty: value.yield_qty,
					yield_unit: value.yield_unit,
					notes: value.notes,
				});
				recipesDb.setRecipeItems(recipe.id, value.items);
				router.back();
			}}
		/>
	);
}
