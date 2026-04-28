import { ProductForm } from "@/components/product-form";
import { Text } from "@/components/ui/text";
import * as productsDb from "@/lib/db/products";
import { useLocalSearchParams, useRouter } from "expo-router";
import { View } from "react-native";

export default function EditProductScreen() {
	const { id } = useLocalSearchParams<{ id: string }>();
	const router = useRouter();
	const product = productsDb.getProductById(id);

	if (!product) {
		return (
			<View className="flex-1 items-center justify-center bg-background">
				<Text>Product not found</Text>
			</View>
		);
	}

	return (
		<ProductForm
			initial={{
				name: product.name,
				sku: product.sku,
				unit: product.unit,
				category_id: product.category_id,
				reorder_point: product.reorder_point,
				unit_cost: product.unit_cost,
				notes: product.notes,
				current_stock: product.current_stock,
			}}
			submitLabel="Save changes"
			onCancel={() => router.back()}
			onSubmit={(input) => {
				productsDb.updateProduct(product.id, {
					name: input.name,
					sku: input.sku,
					unit: input.unit,
					category_id: input.category_id,
					reorder_point: input.reorder_point,
					unit_cost: input.unit_cost,
					notes: input.notes,
				});
				router.back();
			}}
		/>
	);
}
