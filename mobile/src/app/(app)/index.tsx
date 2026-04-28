import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";
import * as movementsDb from "@/lib/db/movements";
import * as productsDb from "@/lib/db/products";
import * as recipesDb from "@/lib/db/recipes";
import * as usersDb from "@/lib/db/users";
import { useNetworkStore } from "@/stores/network-store";
import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { ScrollView, View } from "react-native";

function formatMoney(n: number) {
	return n.toLocaleString(undefined, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	});
}

function KpiCard({
	label,
	value,
	tone = "default",
}: {
	label: string;
	value: string;
	tone?: "default" | "warning" | "danger";
}) {
	const toneClass =
		tone === "danger"
			? "text-destructive"
			: tone === "warning"
				? "text-yellow-700"
				: "text-foreground";
	return (
		<View className="flex-1 rounded-lg border border-border p-3">
			<Text className="text-xs text-muted-foreground">{label}</Text>
			<Text className={`mt-1 text-xl font-bold ${toneClass}`}>{value}</Text>
		</View>
	);
}

export default function HomeScreen() {
	const router = useRouter();
	const [version, setVersion] = useState(0);

	useFocusEffect(
		useCallback(() => {
			setVersion((v) => v + 1);
		}, []),
	);
	void version;

	const user = usersDb.getCachedUser();
	const totalProducts = productsDb.getProductCount();
	const lowStock = productsDb.getLowStockCount();
	const outOfStock = productsDb.getOutOfStockCount();
	const value = productsDb.getInventoryValue();
	const todayMovements = movementsDb.getTodayMovementCount();
	const recipeCount = recipesDb.getRecipeCount();

	const lowStockList = productsDb.listProducts({ status: "low" }).slice(0, 5);
	const outOfStockList = productsDb.listProducts({ status: "out" }).slice(0, 5);
	const recentMovements = movementsDb.listMovements({ limit: 5 });

	const isWifi = useNetworkStore((s) => s.isWifi);
	const isConnected = useNetworkStore((s) => s.isConnected);

	return (
		<ScrollView
			className="flex-1 bg-background"
			contentContainerClassName="gap-4 p-4"
		>
			<View>
				<Text className="text-2xl font-bold">
					Hi{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
				</Text>
				<Text className="text-xs text-muted-foreground">
					{isWifi
						? "Connected"
						: isConnected
							? "Cellular"
							: "Offline · changes saved locally"}
				</Text>
			</View>

			<View className="flex-row gap-2">
				<KpiCard label="Products" value={String(totalProducts)} />
				<KpiCard
					label="Low stock"
					value={String(lowStock)}
					tone={lowStock > 0 ? "warning" : "default"}
				/>
			</View>
			<View className="flex-row gap-2">
				<KpiCard
					label="Out of stock"
					value={String(outOfStock)}
					tone={outOfStock > 0 ? "danger" : "default"}
				/>
				<KpiCard label="Today's moves" value={String(todayMovements)} />
			</View>
			<View className="flex-row gap-2">
				<KpiCard label="Inventory value" value={formatMoney(value)} />
			</View>

			<View className="flex-row gap-2">
				<Button
					label="Add product"
					className="flex-1"
					onPress={() => router.push("/catalog/new")}
				/>
				<Button
					variant="outline"
					label="View catalog"
					className="flex-1"
					onPress={() => router.push("/catalog")}
				/>
			</View>

			<View className="flex-row gap-2">
				<Button
					variant={recipeCount > 0 ? "secondary" : "outline"}
					label={recipeCount > 0 ? "Batch cook" : "Add recipe"}
					className="flex-1"
					onPress={() => router.push("/recipes")}
				/>
				<Button
					variant="outline"
					label="Reports"
					className="flex-1"
					onPress={() => router.push("/reports")}
				/>
			</View>

			{outOfStockList.length > 0 ? (
				<View className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
					<Text className="mb-2 text-sm font-semibold text-destructive">
						Out of stock
					</Text>
					{outOfStockList.map((p) => (
						<View
							key={p.id}
							className="flex-row items-center justify-between py-1.5"
						>
							<Text className="font-medium">{p.name}</Text>
							<Button
								variant="outline"
								size="sm"
								label="Stock in"
								onPress={() => router.push(`/catalog/${p.id}/stock-in`)}
							/>
						</View>
					))}
				</View>
			) : null}

			{lowStockList.length > 0 ? (
				<View className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-3">
					<Text className="mb-2 text-sm font-semibold text-yellow-700">
						Low stock
					</Text>
					{lowStockList.map((p) => (
						<View
							key={p.id}
							className="flex-row items-center justify-between py-1.5"
						>
							<View className="flex-1">
								<Text className="font-medium">{p.name}</Text>
								<Text className="text-xs text-muted-foreground">
									{p.current_stock} {p.unit} · reorder at {p.reorder_point}
								</Text>
							</View>
							<Button
								variant="outline"
								size="sm"
								label="Stock in"
								onPress={() => router.push(`/catalog/${p.id}/stock-in`)}
							/>
						</View>
					))}
				</View>
			) : null}

			<View>
				<View className="mb-2 flex-row items-center justify-between">
					<Text className="text-lg font-semibold">Recent movements</Text>
					<Button
						variant="ghost"
						size="sm"
						label="View all"
						onPress={() => router.push("/movements")}
					/>
				</View>
				{recentMovements.length === 0 ? (
					<Text className="text-sm text-muted-foreground">
						No movements yet. Stock in/out actions will show up here.
					</Text>
				) : (
					<View className="rounded-lg border border-border">
						{recentMovements.map((m, i) => (
							<View
								key={m.id}
								className={`flex-row items-center justify-between p-3 ${
									i > 0 ? "border-t border-border" : ""
								}`}
							>
								<View className="flex-1">
									<Text className="text-sm font-medium">{m.product_name}</Text>
									<Text className="text-xs text-muted-foreground">
										{m.movement_type}
										{m.reason ? ` · ${m.reason}` : ""}
									</Text>
								</View>
								<Text
									className={`font-mono font-semibold ${
										m.quantity >= 0 ? "text-green-700" : "text-destructive"
									}`}
								>
									{m.quantity >= 0 ? "+" : ""}
									{m.quantity} {m.product_unit}
								</Text>
							</View>
						))}
					</View>
				)}
			</View>
		</ScrollView>
	);
}
