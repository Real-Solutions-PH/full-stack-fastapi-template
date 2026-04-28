import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import * as recipesDb from "@/lib/db/recipes";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { Alert, ScrollView, View } from "react-native";

export default function BatchCookScreen() {
	const { id } = useLocalSearchParams<{ id: string }>();
	const router = useRouter();
	const recipe = recipesDb.getRecipeById(id);
	const [multiplierStr, setMultiplierStr] = useState("1");
	const [notes, setNotes] = useState("");

	const multiplier = Number(multiplierStr);
	const validMultiplier =
		multiplierStr.trim() !== "" && !Number.isNaN(multiplier) && multiplier > 0;

	const check = useMemo(
		() =>
			recipe && validMultiplier ? recipesDb.preCookCheck(id, multiplier) : null,
		[recipe, id, multiplier, validMultiplier],
	);

	if (!recipe) {
		return (
			<View className="flex-1 items-center justify-center bg-background">
				<Text>Recipe not found</Text>
			</View>
		);
	}

	const handleCook = () => {
		if (!validMultiplier || !check?.ok) return;
		Alert.alert(
			"Confirm batch cook",
			`Deduct ingredients for ${recipe.name} ×${multiplier}?`,
			[
				{ text: "Cancel", style: "cancel" },
				{
					text: "Cook",
					onPress: () => {
						try {
							recipesDb.executeBatchCook(id, multiplier, notes.trim() || null);
							Alert.alert("Done", "Production run logged.");
							router.back();
						} catch (err) {
							Alert.alert("Error", String(err));
						}
					},
				},
			],
		);
	};

	const yieldEstimate =
		recipe.yield_qty && validMultiplier ? recipe.yield_qty * multiplier : null;

	return (
		<ScrollView
			className="flex-1 bg-background"
			contentContainerClassName="p-4 gap-4"
		>
			<View className="rounded-lg border border-border p-3">
				<Text className="text-xs text-muted-foreground">Recipe</Text>
				<Text className="text-lg font-semibold">{recipe.name}</Text>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Batch multiplier</Text>
				<Input
					value={multiplierStr}
					onChangeText={setMultiplierStr}
					keyboardType="decimal-pad"
					placeholder="1"
					autoFocus
				/>
				{yieldEstimate !== null ? (
					<Text className="text-xs text-muted-foreground">
						Estimated yield: {yieldEstimate} {recipe.yield_unit ?? ""}
					</Text>
				) : null}
			</View>

			<View>
				<Text className="mb-2 text-sm font-semibold">Pre-cook stock check</Text>
				{!validMultiplier ? (
					<Text className="text-xs text-muted-foreground">
						Enter a multiplier to verify stock.
					</Text>
				) : check && check.items.length === 0 ? (
					<Text className="text-xs text-muted-foreground">
						No ingredients on this recipe.
					</Text>
				) : (
					<View
						className={`rounded-lg border p-3 ${
							check?.ok
								? "border-green-500/30 bg-green-500/5"
								: "border-destructive/30 bg-destructive/5"
						}`}
					>
						<Text
							className={`mb-2 text-sm font-semibold ${
								check?.ok ? "text-green-700" : "text-destructive"
							}`}
						>
							{check?.ok
								? "✓ All ingredients available"
								: "✗ Insufficient stock"}
						</Text>
						{check?.items.map((row) => (
							<View
								key={row.product_id}
								className="flex-row items-center justify-between py-1"
							>
								<View className="flex-1">
									<Text className="text-sm font-medium">
										{row.product_name}
									</Text>
									<Text
										className={`text-xs ${
											row.short > 0
												? "text-destructive"
												: "text-muted-foreground"
										}`}
									>
										Need {row.required} {row.product_unit} · have{" "}
										{row.available} {row.product_unit}
										{row.short > 0 ? ` · short ${row.short}` : ""}
									</Text>
								</View>
							</View>
						))}
					</View>
				)}
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Notes</Text>
				<Input value={notes} onChangeText={setNotes} placeholder="optional" />
			</View>

			<View className="mt-2 flex-row gap-2">
				<Button
					variant="outline"
					label="Cancel"
					onPress={() => router.back()}
					className="flex-1"
				/>
				<Button
					label="Cook batch"
					onPress={handleCook}
					disabled={!validMultiplier || !check?.ok}
					className="flex-1"
				/>
			</View>
		</ScrollView>
	);
}
