import { Stack } from "expo-router";

export default function RecipesLayout() {
	return (
		<Stack screenOptions={{ headerShown: true }}>
			<Stack.Screen name="index" options={{ title: "Recipes" }} />
			<Stack.Screen name="new" options={{ title: "New recipe" }} />
			<Stack.Screen name="[id]/index" options={{ title: "Recipe" }} />
			<Stack.Screen name="[id]/edit" options={{ title: "Edit recipe" }} />
			<Stack.Screen name="[id]/cook" options={{ title: "Batch cook" }} />
		</Stack>
	);
}
