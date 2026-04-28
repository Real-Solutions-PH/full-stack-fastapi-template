import { Text } from "@/components/ui/text";
import * as movementsDb from "@/lib/db/movements";
import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { FlatList, Pressable, View } from "react-native";

type Filter = "all" | movementsDb.MovementType;

const filterLabels: Record<Filter, string> = {
	all: "All",
	in: "In",
	out: "Out",
	adjustment: "Adjust",
	batch_cook: "Batch",
};

const movementLabels: Record<movementsDb.MovementType, string> = {
	in: "Stock in",
	out: "Stock out",
	adjustment: "Adjustment",
	batch_cook: "Batch cook",
};

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

export default function MovementsScreen() {
	const router = useRouter();
	const [filter, setFilter] = useState<Filter>("all");
	const [version, setVersion] = useState(0);

	useFocusEffect(
		useCallback(() => {
			setVersion((v) => v + 1);
		}, []),
	);

	void version;
	const movements = movementsDb.listMovements({
		type: filter === "all" ? undefined : filter,
		limit: 200,
	});

	const filters: Filter[] = ["all", "in", "out", "adjustment", "batch_cook"];

	return (
		<View className="flex-1 bg-background p-4">
			<View className="mb-3 flex-row gap-2">
				{filters.map((f) => (
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
							{filterLabels[f]}
						</Text>
					</Pressable>
				))}
			</View>

			<FlatList
				data={movements}
				keyExtractor={(m) => m.id}
				ItemSeparatorComponent={() => <View className="h-px bg-border" />}
				ListEmptyComponent={
					<View className="items-center py-10">
						<Text className="text-muted-foreground">No movements yet</Text>
					</View>
				}
				renderItem={({ item }) => (
					<Pressable
						onPress={() => router.push(`/catalog/${item.product_id}`)}
						className="flex-row items-center justify-between py-3 active:opacity-60"
					>
						<View className="flex-1">
							<Text className="font-medium">{item.product_name}</Text>
							<Text className="text-xs text-muted-foreground">
								{movementLabels[item.movement_type]}
								{item.reason ? ` · ${item.reason}` : ""} ·{" "}
								{formatRelative(item.created_at)}
							</Text>
						</View>
						<Text
							className={`font-mono font-semibold ${
								item.quantity >= 0 ? "text-green-700" : "text-destructive"
							}`}
						>
							{item.quantity >= 0 ? "+" : ""}
							{item.quantity} {item.product_unit}
						</Text>
					</Pressable>
				)}
			/>
		</View>
	);
}
