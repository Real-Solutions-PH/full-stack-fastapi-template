import { StockStatusBadge } from "@/components/stock-status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import * as productsDb from "@/lib/db/products";
import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { FlatList, Pressable, View } from "react-native";

type Filter = "all" | "low" | "out";

export default function CatalogIndexScreen() {
	const router = useRouter();
	const [search, setSearch] = useState("");
	const [filter, setFilter] = useState<Filter>("all");
	const [version, setVersion] = useState(0);

	useFocusEffect(
		useCallback(() => {
			setVersion((v) => v + 1);
		}, []),
	);

	void version;
	const status = filter === "low" ? "low" : filter === "out" ? "out" : "all";
	const products = productsDb.listProducts({
		search: search.trim() || undefined,
		status,
	});

	return (
		<View className="flex-1 bg-background p-4">
			<View className="mb-3 flex-row gap-2">
				<View className="flex-1">
					<Input
						placeholder="Search by name or SKU"
						value={search}
						onChangeText={setSearch}
						autoCapitalize="none"
					/>
				</View>
				<Button label="Add" onPress={() => router.push("/catalog/new")} />
			</View>

			<View className="mb-3 flex-row gap-2">
				{(["all", "low", "out"] as Filter[]).map((f) => (
					<Pressable
						key={f}
						onPress={() => setFilter(f)}
						className={`rounded-full px-3 py-1.5 ${
							filter === f ? "bg-primary" : "bg-muted"
						}`}
					>
						<Text
							className={`text-xs font-medium ${
								filter === f ? "text-primary-foreground" : "text-foreground"
							}`}
						>
							{f === "all" ? "All" : f === "low" ? "Low stock" : "Out of stock"}
						</Text>
					</Pressable>
				))}
			</View>

			<FlatList
				data={products}
				keyExtractor={(p) => p.id}
				ItemSeparatorComponent={() => <View className="h-px bg-border" />}
				ListEmptyComponent={
					<View className="items-center py-10">
						<Text className="text-muted-foreground">No products yet</Text>
						<Text className="mt-1 text-xs text-muted-foreground">
							Tap Add to create one
						</Text>
					</View>
				}
				renderItem={({ item }) => {
					const status = productsDb.stockStatus(item);
					return (
						<Pressable
							onPress={() => router.push(`/catalog/${item.id}`)}
							className="flex-row items-center justify-between py-3 active:opacity-60"
						>
							<View className="flex-1">
								<View className="flex-row items-center gap-2">
									<Text className="font-medium">{item.name}</Text>
									<StockStatusBadge status={status} />
								</View>
								<Text className="text-xs text-muted-foreground">
									{item.current_stock} {item.unit}
									{item.category_name ? ` · ${item.category_name}` : ""}
									{item.sku ? ` · ${item.sku}` : ""}
								</Text>
							</View>
							<Text className="text-muted-foreground">›</Text>
						</Pressable>
					);
				}}
			/>
		</View>
	);
}
