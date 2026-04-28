import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";
import { toCsv } from "@/lib/csv";
import * as movementsDb from "@/lib/db/movements";
import * as productsDb from "@/lib/db/products";
import { useState } from "react";
import { Alert, Platform, ScrollView, Share, View } from "react-native";

type ExportType = "products" | "movements";

function buildProductsCsv() {
	const rows = productsDb.listProducts({ includeArchived: true });
	return toCsv(
		[
			"id",
			"name",
			"sku",
			"category",
			"unit",
			"current_stock",
			"reorder_point",
			"unit_cost",
			"archived",
			"notes",
			"created_at",
		],
		rows.map((p) => [
			p.id,
			p.name,
			p.sku,
			p.category_name,
			p.unit,
			p.current_stock,
			p.reorder_point,
			p.unit_cost,
			p.archived,
			p.notes,
			p.created_at,
		]),
	);
}

function buildMovementsCsv() {
	const rows = movementsDb.listMovements({ limit: 10000 });
	return toCsv(
		[
			"id",
			"created_at",
			"product",
			"unit",
			"type",
			"quantity",
			"balance_after",
			"reason",
			"unit_cost",
			"notes",
		],
		rows.map((m) => [
			m.id,
			m.created_at,
			m.product_name,
			m.product_unit,
			m.movement_type,
			m.quantity,
			m.balance_after,
			m.reason,
			m.unit_cost,
			m.notes,
		]),
	);
}

export default function ExportScreen() {
	const [preview, setPreview] = useState<{
		type: ExportType;
		csv: string;
	} | null>(null);

	const handleExport = async (type: ExportType) => {
		const csv = type === "products" ? buildProductsCsv() : buildMovementsCsv();
		setPreview({ type, csv });
		try {
			if (Platform.OS === "web") {
				const blob = new Blob([csv], { type: "text/csv" });
				const url = URL.createObjectURL(blob);
				const a = document.createElement("a");
				a.href = url;
				a.download = `${type}-${new Date().toISOString().slice(0, 10)}.csv`;
				a.click();
				URL.revokeObjectURL(url);
			} else {
				await Share.share({
					title: `${type}.csv`,
					message: csv,
				});
			}
		} catch (err) {
			Alert.alert("Export failed", String(err));
		}
	};

	return (
		<ScrollView
			className="flex-1 bg-background"
			contentContainerClassName="p-4 gap-4"
		>
			<View>
				<Text className="text-2xl font-bold">Export data</Text>
				<Text className="mt-1 text-sm text-muted-foreground">
					Download a CSV snapshot for offline safekeeping.
				</Text>
			</View>

			<Button
				label="Export products"
				onPress={() => handleExport("products")}
			/>
			<Button
				label="Export stock movements"
				onPress={() => handleExport("movements")}
			/>

			{preview ? (
				<View className="rounded-lg border border-border p-3">
					<Text className="mb-2 text-xs font-semibold text-muted-foreground">
						Preview ({preview.type}) — first 1KB
					</Text>
					<Text className="font-mono text-xs">
						{preview.csv.slice(0, 1024)}
						{preview.csv.length > 1024 ? "\n…" : ""}
					</Text>
				</View>
			) : null}
		</ScrollView>
	);
}
