import { Stack } from "expo-router";

export default function CatalogLayout() {
	return (
		<Stack screenOptions={{ headerShown: true }}>
			<Stack.Screen name="index" options={{ title: "Catalog" }} />
			<Stack.Screen name="new" options={{ title: "New product" }} />
			<Stack.Screen name="[id]/index" options={{ title: "Product" }} />
			<Stack.Screen name="[id]/edit" options={{ title: "Edit product" }} />
			<Stack.Screen name="[id]/stock-in" options={{ title: "Stock in" }} />
			<Stack.Screen name="[id]/stock-out" options={{ title: "Stock out" }} />
			<Stack.Screen name="[id]/adjust" options={{ title: "Adjust stock" }} />
		</Stack>
	);
}
