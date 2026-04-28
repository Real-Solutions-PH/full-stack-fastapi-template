import { Text } from "@/components/ui/text";
import type { StockStatus } from "@/lib/db/products";
import { cn } from "@/lib/utils";
import { View } from "react-native";

const labels: Record<StockStatus, string> = {
	out: "Out of stock",
	low: "Low",
	healthy: "OK",
};

const styles: Record<StockStatus, { wrap: string; text: string }> = {
	out: { wrap: "bg-destructive/15", text: "text-destructive" },
	low: { wrap: "bg-yellow-500/15", text: "text-yellow-700" },
	healthy: { wrap: "bg-green-500/15", text: "text-green-700" },
};

export function StockStatusBadge({
	status,
	className,
}: {
	status: StockStatus;
	className?: string;
}) {
	const s = styles[status];
	return (
		<View className={cn("rounded-full px-2 py-0.5", s.wrap, className)}>
			<Text className={cn("text-xs font-semibold", s.text)}>
				{labels[status]}
			</Text>
		</View>
	);
}
