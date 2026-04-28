import { RecipeForm } from "@/components/recipe-form";
import * as recipesDb from "@/lib/db/recipes";
import { useRouter } from "expo-router";

export default function NewRecipeScreen() {
	const router = useRouter();
	return (
		<RecipeForm
			submitLabel="Create recipe"
			onCancel={() => router.back()}
			onSubmit={(value) => {
				const id = crypto.randomUUID();
				recipesDb.insertRecipe(id, {
					name: value.name,
					yield_qty: value.yield_qty,
					yield_unit: value.yield_unit,
					notes: value.notes,
				});
				recipesDb.setRecipeItems(id, value.items);
				router.replace(`/recipes/${id}`);
			}}
		/>
	);
}
