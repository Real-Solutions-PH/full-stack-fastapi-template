import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import * as categoriesDb from "@/lib/db/categories";
import { useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, FlatList, Pressable, View } from "react-native";

const COLOR_OPTIONS = [
	{ name: "Blue", value: "#3b82f6" },
	{ name: "Green", value: "#22c55e" },
	{ name: "Red", value: "#ef4444" },
	{ name: "Yellow", value: "#eab308" },
	{ name: "Purple", value: "#a855f7" },
	{ name: "Pink", value: "#ec4899" },
];

export default function CategoriesScreen() {
	const [version, setVersion] = useState(0);
	const [name, setName] = useState("");
	const [color, setColor] = useState<string>(COLOR_OPTIONS[0].value);

	useFocusEffect(
		useCallback(() => {
			setVersion((v) => v + 1);
		}, []),
	);

	const categories = categoriesDb.listCategories(true);
	void version;

	const handleAdd = () => {
		const trimmed = name.trim();
		if (!trimmed) return;
		categoriesDb.insertCategory({
			id: crypto.randomUUID(),
			name: trimmed,
			color,
		});
		setName("");
		setVersion((v) => v + 1);
	};

	const handleDelete = (id: string, n: string) => {
		Alert.alert("Delete category", `Delete "${n}"?`, [
			{ text: "Cancel", style: "cancel" },
			{
				text: "Delete",
				style: "destructive",
				onPress: () => {
					categoriesDb.deleteCategory(id);
					setVersion((v) => v + 1);
				},
			},
		]);
	};

	return (
		<View className="flex-1 bg-background">
			<View className="border-b border-border p-4">
				<View className="gap-2">
					<Input
						value={name}
						onChangeText={setName}
						placeholder="Category name"
					/>
					<View className="flex-row flex-wrap gap-2">
						{COLOR_OPTIONS.map((c) => (
							<Pressable
								key={c.value}
								onPress={() => setColor(c.value)}
								className={`h-8 w-8 rounded-full border-2 ${
									color === c.value ? "border-foreground" : "border-transparent"
								}`}
								style={{ backgroundColor: c.value }}
							/>
						))}
					</View>
					<Button
						label="Add category"
						onPress={handleAdd}
						disabled={!name.trim()}
					/>
				</View>
			</View>

			<FlatList
				className="flex-1"
				data={categories}
				keyExtractor={(c) => c.id}
				ItemSeparatorComponent={() => <View className="h-px bg-border" />}
				ListEmptyComponent={
					<View className="items-center py-10">
						<Text className="text-muted-foreground">No categories yet</Text>
					</View>
				}
				renderItem={({ item }) => (
					<View className="flex-row items-center justify-between p-4">
						<View className="flex-row items-center gap-3">
							{item.color ? (
								<View
									className="h-4 w-4 rounded-full"
									style={{ backgroundColor: item.color }}
								/>
							) : null}
							<Text className="font-medium">{item.name}</Text>
						</View>
						<Pressable
							onPress={() => handleDelete(item.id, item.name)}
							className="rounded p-2 active:opacity-60"
						>
							<Text className="text-sm text-destructive">Delete</Text>
						</Pressable>
					</View>
				)}
			/>
		</View>
	);
}
