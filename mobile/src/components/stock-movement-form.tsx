import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import * as movementsDb from "@/lib/db/movements";
import type { LocalProduct } from "@/lib/db/products";
import { useState } from "react";
import { Alert, Pressable, ScrollView, View } from "react-native";

const REASONS_IN = ["delivery", "return", "transfer_in"] as const;
const REASONS_OUT = [
	"production",
	"spoilage",
	"damaged",
	"sale",
	"transfer_out",
] as const;
const REASONS_ADJ = ["recount", "correction", "opening_stock"] as const;

type Mode = "in" | "out" | "adjustment";

const titles: Record<Mode, string> = {
	in: "Stock in",
	out: "Stock out",
	adjustment: "Adjust stock",
};

const ctaLabels: Record<Mode, string> = {
	in: "Record delivery",
	out: "Record stock out",
	adjustment: "Save adjustment",
};

export function StockMovementForm({
	product,
	mode,
	onDone,
	onCancel,
}: {
	product: LocalProduct;
	mode: Mode;
	onDone: () => void;
	onCancel?: () => void;
}) {
	const [quantity, setQuantity] = useState("");
	const reasons =
		mode === "in" ? REASONS_IN : mode === "out" ? REASONS_OUT : REASONS_ADJ;
	const [reason, setReason] = useState<string>(reasons[0]);
	const [unitCost, setUnitCost] = useState(
		product.unit_cost != null ? String(product.unit_cost) : "",
	);
	const [notes, setNotes] = useState("");

	const qty = Number(quantity);
	const validQty = quantity.trim() !== "" && !Number.isNaN(qty);
	const valid =
		mode === "adjustment" ? validQty && qty >= 0 : validQty && qty > 0;

	const projectedBalance =
		mode === "in"
			? product.current_stock + (validQty ? qty : 0)
			: mode === "out"
				? product.current_stock - (validQty ? qty : 0)
				: validQty
					? qty
					: product.current_stock;

	const insufficientOut =
		mode === "out" && validQty && product.current_stock < qty;

	const handleSubmit = () => {
		if (!valid) return;
		try {
			movementsDb.recordMovement({
				product_id: product.id,
				movement_type: mode,
				quantity: qty,
				reason,
				unit_cost: unitCost.trim() ? Number(unitCost) : null,
				notes: notes.trim() || null,
			});
			onDone();
		} catch (err) {
			if (err instanceof movementsDb.InsufficientStockError) {
				Alert.alert(
					"Insufficient stock",
					`Only ${err.available} ${product.unit} available, ${err.requested} requested.`,
				);
			} else {
				Alert.alert("Error", String(err));
			}
		}
	};

	return (
		<ScrollView
			className="flex-1 bg-background"
			contentContainerClassName="p-4 gap-4"
		>
			<View className="rounded-lg border border-border p-3">
				<Text className="text-xs text-muted-foreground">{product.name}</Text>
				<Text className="text-lg font-semibold">
					Current: {product.current_stock} {product.unit}
				</Text>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">
					{mode === "adjustment" ? "New stock level" : "Quantity"} (
					{product.unit})
				</Text>
				<Input
					value={quantity}
					onChangeText={setQuantity}
					keyboardType="decimal-pad"
					placeholder="0"
					autoFocus
				/>
				{validQty ? (
					<Text
						className={`text-xs ${
							insufficientOut ? "text-destructive" : "text-muted-foreground"
						}`}
					>
						New balance: {projectedBalance} {product.unit}
						{insufficientOut ? " (insufficient stock)" : ""}
					</Text>
				) : null}
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Reason</Text>
				<View className="flex-row flex-wrap gap-2">
					{reasons.map((r) => (
						<Pressable
							key={r}
							onPress={() => setReason(r)}
							className={`rounded-full px-3 py-1.5 ${
								reason === r ? "bg-primary" : "bg-muted"
							}`}
						>
							<Text
								className={`text-xs font-medium ${
									reason === r ? "text-primary-foreground" : "text-foreground"
								}`}
							>
								{r.replace(/_/g, " ")}
							</Text>
						</Pressable>
					))}
				</View>
			</View>

			{mode === "in" ? (
				<View className="gap-1.5">
					<Text className="text-sm font-medium">Unit cost</Text>
					<Input
						value={unitCost}
						onChangeText={setUnitCost}
						keyboardType="decimal-pad"
						placeholder="optional"
					/>
				</View>
			) : null}

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Notes</Text>
				<Input value={notes} onChangeText={setNotes} placeholder="optional" />
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
					label={ctaLabels[mode]}
					onPress={handleSubmit}
					disabled={!valid || insufficientOut}
					className="flex-1"
				/>
			</View>

			<Text className="text-center text-xs text-muted-foreground">
				{titles[mode]}
			</Text>
		</ScrollView>
	);
}
