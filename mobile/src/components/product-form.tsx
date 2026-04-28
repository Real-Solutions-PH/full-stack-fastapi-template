import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import * as categoriesDb from "@/lib/db/categories";
import type { ProductInput } from "@/lib/db/products";
import { useMemo, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";

const COMMON_UNITS = ["pc", "kg", "g", "L", "ml", "box", "pack"] as const;

export function ProductForm({
	initial,
	submitLabel,
	onSubmit,
	onCancel,
}: {
	initial?: Partial<ProductInput & { current_stock: number }>;
	submitLabel: string;
	onSubmit: (input: ProductInput & { current_stock?: number }) => void;
	onCancel?: () => void;
}) {
	const [name, setName] = useState(initial?.name ?? "");
	const [sku, setSku] = useState(initial?.sku ?? "");
	const [unit, setUnit] = useState(initial?.unit ?? "pc");
	const [reorderPoint, setReorderPoint] = useState(
		String(initial?.reorder_point ?? "0"),
	);
	const [unitCost, setUnitCost] = useState(
		initial?.unit_cost != null ? String(initial.unit_cost) : "",
	);
	const [openingStock, setOpeningStock] = useState(
		initial?.current_stock != null ? String(initial.current_stock) : "0",
	);
	const [notes, setNotes] = useState(initial?.notes ?? "");
	const [categoryId, setCategoryId] = useState<string | null>(
		initial?.category_id ?? null,
	);

	const categories = useMemo(() => categoriesDb.listCategories(), []);

	const valid = name.trim().length > 0 && unit.trim().length > 0;

	const handleSubmit = () => {
		if (!valid) return;
		onSubmit({
			name: name.trim(),
			sku: sku.trim() || null,
			unit: unit.trim(),
			category_id: categoryId,
			reorder_point: Number(reorderPoint) || 0,
			unit_cost: unitCost.trim() ? Number(unitCost) : null,
			current_stock: Number(openingStock) || 0,
			notes: notes.trim() || null,
		});
	};

	return (
		<ScrollView
			className="flex-1 bg-background"
			contentContainerClassName="p-4 gap-4"
		>
			<View className="gap-1.5">
				<Text className="text-sm font-medium">Name *</Text>
				<Input
					value={name}
					onChangeText={setName}
					placeholder="e.g., Olive Oil"
				/>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">SKU</Text>
				<Input
					value={sku ?? ""}
					onChangeText={setSku}
					placeholder="optional"
					autoCapitalize="characters"
				/>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Unit *</Text>
				<View className="flex-row flex-wrap gap-2">
					{COMMON_UNITS.map((u) => (
						<Pressable
							key={u}
							onPress={() => setUnit(u)}
							className={`rounded-full px-3 py-1.5 ${
								unit === u ? "bg-primary" : "bg-muted"
							}`}
						>
							<Text
								className={`text-xs font-medium ${
									unit === u ? "text-primary-foreground" : "text-foreground"
								}`}
							>
								{u}
							</Text>
						</Pressable>
					))}
				</View>
				<Input value={unit} onChangeText={setUnit} placeholder="custom unit" />
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Category</Text>
				{categories.length === 0 ? (
					<Text className="text-xs text-muted-foreground">
						No categories yet. Add via Settings.
					</Text>
				) : (
					<View className="flex-row flex-wrap gap-2">
						<Pressable
							onPress={() => setCategoryId(null)}
							className={`rounded-full px-3 py-1.5 ${
								categoryId === null ? "bg-primary" : "bg-muted"
							}`}
						>
							<Text
								className={`text-xs font-medium ${
									categoryId === null
										? "text-primary-foreground"
										: "text-foreground"
								}`}
							>
								None
							</Text>
						</Pressable>
						{categories.map((c) => (
							<Pressable
								key={c.id}
								onPress={() => setCategoryId(c.id)}
								className={`rounded-full px-3 py-1.5 ${
									categoryId === c.id ? "bg-primary" : "bg-muted"
								}`}
							>
								<Text
									className={`text-xs font-medium ${
										categoryId === c.id
											? "text-primary-foreground"
											: "text-foreground"
									}`}
								>
									{c.name}
								</Text>
							</Pressable>
						))}
					</View>
				)}
			</View>

			{initial?.current_stock === undefined ? (
				<View className="gap-1.5">
					<Text className="text-sm font-medium">Opening stock</Text>
					<Input
						value={openingStock}
						onChangeText={setOpeningStock}
						keyboardType="decimal-pad"
						placeholder="0"
					/>
				</View>
			) : null}

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Reorder point</Text>
				<Input
					value={reorderPoint}
					onChangeText={setReorderPoint}
					keyboardType="decimal-pad"
					placeholder="0"
				/>
				<Text className="text-xs text-muted-foreground">
					Alert when stock falls to or below this level
				</Text>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Unit cost</Text>
				<Input
					value={unitCost}
					onChangeText={setUnitCost}
					keyboardType="decimal-pad"
					placeholder="optional"
				/>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Notes</Text>
				<Input
					value={notes ?? ""}
					onChangeText={setNotes}
					placeholder="optional"
				/>
			</View>

			<View className="mt-2 flex-row gap-2">
				{onCancel ? (
					<Button
						variant="outline"
						label="Cancel"
						onPress={onCancel}
						className="flex-1"
					/>
				) : null}
				<Button
					label={submitLabel}
					onPress={handleSubmit}
					disabled={!valid}
					className="flex-1"
				/>
			</View>
		</ScrollView>
	);
}
