import { StockStatusBadge } from "@/components/stock-status-badge";
import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";
import * as movementsDb from "@/lib/db/movements";
import * as productsDb from "@/lib/db/products";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, Pressable, ScrollView, View } from "react-native";

function formatMoney(n: number) {
	return n.toLocaleString(undefined, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	});
}

function formatRelative(iso: string) {
	const d = new Date(`${iso.replace(" ", "T")}Z`);
	const diff = Date.now() - d.getTime();
	const mins = Math.round(diff / 60000);
	if (mins < 1) return "just now";
	if (mins < 60) return `${mins}m ago`;
	const hours = Math.round(mins / 60);
	if (hours < 24) return `${hours}h ago`;
	const days = Math.round(hours / 24);
	return `${days}d ago`;
}

const movementLabels: Record<movementsDb.MovementType, string> = {
	in: "Stock in",
	out: "Stock out",
	adjustment: "Adjustment",
	batch_cook: "Batch cook",
};

export default function ProductDetailScreen() {
	const { id } = useLocalSearchParams<{ id: string }>();
	const router = useRouter();
	const [version, setVersion] = useState(0);

	useFocusEffect(
		useCallback(() => {
			setVersion((v) => v + 1);
		}, []),
	);

	const product = productsDb.getProductById(id);
	const movements = movementsDb.listMovements({
		productId: id,
		sinceDays: 30,
		limit: 50,
	});
	void version;

	if (!product) {
		return (
			<View className="flex-1 items-center justify-center bg-background p-6">
				<Text>Product not found</Text>
				<Button
					label="Back"
					variant="outline"
					className="mt-4"
					onPress={() => router.back()}
				/>
			</View>
		);
	}

	const status = productsDb.stockStatus(product);
	const value = product.current_stock * (product.unit_cost ?? 0);

	const handleArchive = () => {
		Alert.alert("Archive product", `Archive "${product.name}"?`, [
			{ text: "Cancel", style: "cancel" },
			{
				text: "Archive",
				style: "destructive",
				onPress: () => {
					productsDb.updateProduct(product.id, { archived: 1 });
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
				<View className="flex-row items-center gap-2">
					<Text className="text-2xl font-bold">{product.name}</Text>
					<StockStatusBadge status={status} />
				</View>
				{product.sku ? (
					<Text className="text-xs text-muted-foreground">
						SKU: {product.sku}
					</Text>
				) : null}
				{product.category_name ? (
					<Text className="text-xs text-muted-foreground">
						{product.category_name}
					</Text>
				) : null}
			</View>

			<View className="rounded-lg border border-border p-4">
				<Text className="text-xs text-muted-foreground">Current stock</Text>
				<Text className="mt-1 text-3xl font-bold">
					{product.current_stock} {product.unit}
				</Text>
				<View className="mt-2 flex-row gap-4">
					<View>
						<Text className="text-xs text-muted-foreground">Reorder at</Text>
						<Text className="text-sm font-medium">
							{product.reorder_point} {product.unit}
						</Text>
					</View>
					{product.unit_cost != null ? (
						<View>
							<Text className="text-xs text-muted-foreground">Unit cost</Text>
							<Text className="text-sm font-medium">
								{formatMoney(product.unit_cost)}
							</Text>
						</View>
					) : null}
					{product.unit_cost != null ? (
						<View>
							<Text className="text-xs text-muted-foreground">Value</Text>
							<Text className="text-sm font-medium">{formatMoney(value)}</Text>
						</View>
					) : null}
				</View>
			</View>

			<View className="flex-row gap-2">
				<Button
					label="Stock in"
					className="flex-1"
					onPress={() => router.push(`/catalog/${product.id}/stock-in`)}
				/>
				<Button
					label="Stock out"
					variant="secondary"
					className="flex-1"
					onPress={() => router.push(`/catalog/${product.id}/stock-out`)}
				/>
			</View>
			<View className="flex-row gap-2">
				<Button
					label="Adjust"
					variant="outline"
					className="flex-1"
					onPress={() => router.push(`/catalog/${product.id}/adjust`)}
				/>
				<Button
					label="Edit"
					variant="outline"
					className="flex-1"
					onPress={() => router.push(`/catalog/${product.id}/edit`)}
				/>
			</View>

			{product.notes ? (
				<View className="rounded-lg border border-border p-3">
					<Text className="text-xs text-muted-foreground">Notes</Text>
					<Text className="mt-1 text-sm">{product.notes}</Text>
				</View>
			) : null}

			<View>
				<Text className="mb-2 text-lg font-semibold">
					Recent movements (30d)
				</Text>
				{movements.length === 0 ? (
					<Text className="text-sm text-muted-foreground">
						No movements yet
					</Text>
				) : (
					<View className="rounded-lg border border-border">
						{movements.map((m, i) => (
							<View
								key={m.id}
								className={`flex-row items-center justify-between p-3 ${
									i > 0 ? "border-t border-border" : ""
								}`}
							>
								<View className="flex-1">
									<Text className="text-sm font-medium">
										{movementLabels[m.movement_type]}
										{m.reason ? ` · ${m.reason}` : ""}
									</Text>
									<Text className="text-xs text-muted-foreground">
										{formatRelative(m.created_at)} · balance {m.balance_after}{" "}
										{product.unit}
									</Text>
								</View>
								<Text
									className={`font-mono font-semibold ${
										m.quantity >= 0 ? "text-green-700" : "text-destructive"
									}`}
								>
									{m.quantity >= 0 ? "+" : ""}
									{m.quantity} {product.unit}
								</Text>
							</View>
						))}
					</View>
				)}
			</View>

			<Pressable onPress={handleArchive} className="items-center py-2">
				<Text className="text-sm text-destructive">Archive product</Text>
			</Pressable>
		</ScrollView>
	);
}
