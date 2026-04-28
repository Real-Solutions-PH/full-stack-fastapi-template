import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import * as productsDb from "@/lib/db/products";
import type { RecipeInput } from "@/lib/db/recipes";
import { useMemo, useState } from "react";
import { Alert, Pressable, ScrollView, View } from "react-native";

export interface RecipeFormValue extends RecipeInput {
	items: { product_id: string; quantity: number }[];
}

export function RecipeForm({
	initial,
	submitLabel,
	onSubmit,
	onCancel,
}: {
	initial?: Partial<RecipeFormValue>;
	submitLabel: string;
	onSubmit: (value: RecipeFormValue) => void;
	onCancel?: () => void;
}) {
	const allProducts = useMemo(() => productsDb.listProducts(), []);
	const [name, setName] = useState(initial?.name ?? "");
	const [yieldQty, setYieldQty] = useState(
		initial?.yield_qty != null ? String(initial.yield_qty) : "",
	);
	const [yieldUnit, setYieldUnit] = useState(initial?.yield_unit ?? "");
	const [notes, setNotes] = useState(initial?.notes ?? "");
	const [items, setItems] = useState<
		{ product_id: string; quantity: string }[]
	>(
		(initial?.items ?? []).map((i) => ({
			product_id: i.product_id,
			quantity: String(i.quantity),
		})),
	);
	const [picker, setPicker] = useState(false);

	const productMap = useMemo(() => {
		const m = new Map<string, (typeof allProducts)[number]>();
		for (const p of allProducts) m.set(p.id, p);
		return m;
	}, [allProducts]);

	const usedIds = new Set(items.map((i) => i.product_id));
	const available = allProducts.filter((p) => !usedIds.has(p.id));

	const valid =
		name.trim().length > 0 &&
		items.length > 0 &&
		items.every((i) => {
			const q = Number(i.quantity);
			return !Number.isNaN(q) && q > 0;
		});

	const handleAddItem = (productId: string) => {
		setItems((prev) => [...prev, { product_id: productId, quantity: "1" }]);
		setPicker(false);
	};

	const handleRemoveItem = (productId: string) => {
		setItems((prev) => prev.filter((i) => i.product_id !== productId));
	};

	const handleQtyChange = (productId: string, q: string) => {
		setItems((prev) =>
			prev.map((i) => (i.product_id === productId ? { ...i, quantity: q } : i)),
		);
	};

	const handleSubmit = () => {
		if (!valid) {
			Alert.alert("Incomplete", "Add a name and at least one ingredient.");
			return;
		}
		onSubmit({
			name: name.trim(),
			yield_qty: yieldQty.trim() ? Number(yieldQty) : null,
			yield_unit: yieldUnit.trim() || null,
			notes: notes.trim() || null,
			items: items.map((i) => ({
				product_id: i.product_id,
				quantity: Number(i.quantity),
			})),
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
					placeholder="e.g., Chicken Adobo"
				/>
			</View>

			<View className="flex-row gap-2">
				<View className="flex-1 gap-1.5">
					<Text className="text-sm font-medium">Yield qty</Text>
					<Input
						value={yieldQty}
						onChangeText={setYieldQty}
						keyboardType="decimal-pad"
						placeholder="optional"
					/>
				</View>
				<View className="flex-1 gap-1.5">
					<Text className="text-sm font-medium">Yield unit</Text>
					<Input
						value={yieldUnit ?? ""}
						onChangeText={setYieldUnit}
						placeholder="e.g., portions"
					/>
				</View>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Notes</Text>
				<Input
					value={notes ?? ""}
					onChangeText={setNotes}
					placeholder="optional"
				/>
			</View>

			<View className="gap-2">
				<View className="flex-row items-center justify-between">
					<Text className="text-sm font-medium">Ingredients *</Text>
					<Button
						size="sm"
						variant="outline"
						label={picker ? "Close" : "Add ingredient"}
						onPress={() => setPicker((p) => !p)}
						disabled={available.length === 0 && !picker}
					/>
				</View>

				{picker ? (
					available.length === 0 ? (
						<Text className="text-xs text-muted-foreground">
							All products already added.
						</Text>
					) : (
						<View className="rounded-lg border border-border">
							{available.map((p, i) => (
								<Pressable
									key={p.id}
									onPress={() => handleAddItem(p.id)}
									className={`p-3 active:opacity-60 ${
										i > 0 ? "border-t border-border" : ""
									}`}
								>
									<Text className="font-medium">{p.name}</Text>
									<Text className="text-xs text-muted-foreground">
										{p.current_stock} {p.unit} on hand
									</Text>
								</Pressable>
							))}
						</View>
					)
				) : null}

				{items.length === 0 ? (
					<Text className="text-xs text-muted-foreground">
						No ingredients yet. Tap Add ingredient.
					</Text>
				) : (
					<View className="rounded-lg border border-border">
						{items.map((i, idx) => {
							const p = productMap.get(i.product_id);
							if (!p) return null;
							return (
								<View
									key={i.product_id}
									className={`gap-2 p-3 ${
										idx > 0 ? "border-t border-border" : ""
									}`}
								>
									<View className="flex-row items-center justify-between">
										<Text className="font-medium">{p.name}</Text>
										<Pressable
											onPress={() => handleRemoveItem(i.product_id)}
											className="active:opacity-60"
										>
											<Text className="text-sm text-destructive">Remove</Text>
										</Pressable>
									</View>
									<View className="flex-row items-center gap-2">
										<Input
											value={i.quantity}
											onChangeText={(q) => handleQtyChange(i.product_id, q)}
											keyboardType="decimal-pad"
											placeholder="qty"
											className="flex-1"
										/>
										<Text className="text-sm text-muted-foreground">
											{p.unit} per batch
										</Text>
									</View>
								</View>
							);
						})}
					</View>
				)}
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
