import { StockMovementForm } from "@/components/stock-movement-form";
import { Text } from "@/components/ui/text";
import * as productsDb from "@/lib/db/products";
import { useLocalSearchParams, useRouter } from "expo-router";
import { View } from "react-native";

export default function StockOutScreen() {
	const { id } = useLocalSearchParams<{ id: string }>();
	const router = useRouter();
	const product = productsDb.getProductById(id);
	if (!product)
		return (
			<View className="flex-1 items-center justify-center">
				<Text>Product not found</Text>
			</View>
		);
	return (
		<StockMovementForm
			product={product}
			mode="out"
			onCancel={() => router.back()}
			onDone={() => router.back()}
		/>
	);
}
