import { Text } from "@/components/ui/text";
import * as productsDb from "@/lib/db/products";
import * as reportsDb from "@/lib/db/reports";
import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useMemo, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";

type Range = "7d" | "30d" | "90d" | "all";
const RANGE_LABELS: Record<Range, string> = {
	"7d": "7 days",
	"30d": "30 days",
	"90d": "90 days",
	all: "All time",
};

function rangeToFrom(r: Range): string | undefined {
	if (r === "all") return undefined;
	const days = r === "7d" ? 7 : r === "30d" ? 30 : 90;
	const d = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
	return d.toISOString().slice(0, 19).replace("T", " ");
}

function formatMoney(n: number) {
	return n.toLocaleString(undefined, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	});
}

export default function ReportsScreen() {
	const router = useRouter();
	const [range, setRange] = useState<Range>("30d");
	const [version, setVersion] = useState(0);

	useFocusEffect(
		useCallback(() => {
			setVersion((v) => v + 1);
		}, []),
	);
	void version;

	const from = useMemo(() => rangeToFrom(range), [range]);
	const summary = reportsDb.movementSummary(from);
	const valueByCat = reportsDb.valueByCategory();
	const waste = reportsDb.wasteReport(from);
	const top = reportsDb.topConsumed(from, undefined, 10);
	const lowStock = productsDb.listProducts({ status: "low" });
	const outOfStock = productsDb.listProducts({ status: "out" });
	const totalValue = productsDb.getInventoryValue();

	const wasteCost = waste.reduce((s, r) => s + r.cost_lost, 0);

	return (
		<ScrollView
			className="flex-1 bg-background"
			contentContainerClassName="gap-4 p-4"
		>
			<View className="flex-row gap-2">
				{(["7d", "30d", "90d", "all"] as Range[]).map((r) => (
					<Pressable
						key={r}
						onPress={() => setRange(r)}
						className={`rounded-full px-3 py-1.5 ${
							range === r ? "bg-primary" : "bg-muted"
						}`}
					>
						<Text
							className={`text-xs font-medium ${
								range === r ? "text-primary-foreground" : "text-foreground"
							}`}
						>
							{RANGE_LABELS[r]}
						</Text>
					</Pressable>
				))}
			</View>

			<View className="rounded-lg border border-border p-3">
				<Text className="text-xs text-muted-foreground">Inventory value</Text>
				<Text className="mt-1 text-2xl font-bold">
					{formatMoney(totalValue)}
				</Text>
			</View>

			<View className="flex-row gap-2">
				<View className="flex-1 rounded-lg border border-border p-3">
					<Text className="text-xs text-muted-foreground">Total in</Text>
					<Text className="mt-1 text-lg font-bold text-green-700">
						+{summary.total_in.toFixed(2)}
					</Text>
				</View>
				<View className="flex-1 rounded-lg border border-border p-3">
					<Text className="text-xs text-muted-foreground">Total out</Text>
					<Text className="mt-1 text-lg font-bold text-destructive">
						-{summary.total_out.toFixed(2)}
					</Text>
				</View>
				<View className="flex-1 rounded-lg border border-border p-3">
					<Text className="text-xs text-muted-foreground">Movements</Text>
					<Text className="mt-1 text-lg font-bold">
						{summary.movement_count}
					</Text>
				</View>
			</View>

			<View>
				<Text className="mb-2 text-lg font-semibold">Value by category</Text>
				{valueByCat.length === 0 ? (
					<Text className="text-sm text-muted-foreground">No data</Text>
				) : (
					<View className="rounded-lg border border-border">
						{valueByCat.map((row, i) => (
							<View
								key={row.category_id ?? "uncat"}
								className={`flex-row items-center justify-between p-3 ${
									i > 0 ? "border-t border-border" : ""
								}`}
							>
								<View className="flex-1">
									<Text className="text-sm font-medium">
										{row.category_name ?? "Uncategorized"}
									</Text>
									<Text className="text-xs text-muted-foreground">
										{row.product_count} product
										{row.product_count === 1 ? "" : "s"}
									</Text>
								</View>
								<Text className="font-mono text-sm font-semibold">
									{formatMoney(row.total_value)}
								</Text>
							</View>
						))}
					</View>
				)}
			</View>

			<View>
				<Text className="mb-2 text-lg font-semibold">
					Waste / shrinkage ({RANGE_LABELS[range]})
				</Text>
				{waste.length === 0 ? (
					<Text className="text-sm text-muted-foreground">
						No spoilage or damage logged.
					</Text>
				) : (
					<View className="rounded-lg border border-destructive/30 bg-destructive/5">
						<View className="flex-row items-center justify-between border-b border-destructive/30 p-3">
							<Text className="text-sm font-semibold text-destructive">
								Total cost lost
							</Text>
							<Text className="font-mono font-bold text-destructive">
								{formatMoney(wasteCost)}
							</Text>
						</View>
						{waste.map((row, i) => (
							<View
								key={row.product_id}
								className={`flex-row items-center justify-between p-3 ${
									i > 0 ? "border-t border-destructive/20" : ""
								}`}
							>
								<View className="flex-1">
									<Text className="text-sm font-medium">
										{row.product_name}
									</Text>
									<Text className="text-xs text-muted-foreground">
										{row.quantity_lost} {row.product_unit} lost
									</Text>
								</View>
								<Text className="font-mono text-sm font-semibold text-destructive">
									{formatMoney(row.cost_lost)}
								</Text>
							</View>
						))}
					</View>
				)}
			</View>

			<View>
				<Text className="mb-2 text-lg font-semibold">
					Top consumed ({RANGE_LABELS[range]})
				</Text>
				{top.length === 0 ? (
					<Text className="text-sm text-muted-foreground">
						No usage logged.
					</Text>
				) : (
					<View className="rounded-lg border border-border">
						{top.map((row, i) => (
							<Pressable
								key={row.product_id}
								onPress={() => router.push(`/catalog/${row.product_id}`)}
								className={`flex-row items-center justify-between p-3 active:opacity-60 ${
									i > 0 ? "border-t border-border" : ""
								}`}
							>
								<Text className="flex-1 text-sm font-medium">
									{row.product_name}
								</Text>
								<Text className="font-mono text-sm font-semibold">
									{row.total_consumed} {row.product_unit}
								</Text>
							</Pressable>
						))}
					</View>
				)}
			</View>

			<View>
				<Text className="mb-2 text-lg font-semibold">Reorder list</Text>
				{lowStock.length + outOfStock.length === 0 ? (
					<Text className="text-sm text-muted-foreground">
						No products below reorder point.
					</Text>
				) : (
					<View className="rounded-lg border border-yellow-500/30 bg-yellow-500/5">
						{[...outOfStock, ...lowStock].map((p, i) => (
							<Pressable
								key={p.id}
								onPress={() => router.push(`/catalog/${p.id}`)}
								className={`flex-row items-center justify-between p-3 active:opacity-60 ${
									i > 0 ? "border-t border-yellow-500/20" : ""
								}`}
							>
								<View className="flex-1">
									<Text className="text-sm font-medium">{p.name}</Text>
									<Text className="text-xs text-muted-foreground">
										{p.current_stock} {p.unit} · reorder at {p.reorder_point}
									</Text>
								</View>
								<Text
									className={`text-xs font-semibold ${
										p.current_stock <= 0
											? "text-destructive"
											: "text-yellow-700"
									}`}
								>
									{p.current_stock <= 0 ? "OUT" : "LOW"}
								</Text>
							</Pressable>
						))}
					</View>
				)}
			</View>
		</ScrollView>
	);
}
