import { ProductForm } from "@/components/product-form";
import * as movementsDb from "@/lib/db/movements";
import * as productsDb from "@/lib/db/products";
import { useRouter } from "expo-router";

export default function NewProductScreen() {
	const router = useRouter();

	return (
		<ProductForm
			submitLabel="Create product"
			onCancel={() => router.back()}
			onSubmit={(input) => {
				const id = crypto.randomUUID();
				const opening = input.current_stock ?? 0;
				productsDb.insertProduct(id, { ...input, current_stock: 0 });
				if (opening !== 0) {
					movementsDb.recordMovement({
						product_id: id,
						movement_type: "adjustment",
						quantity: opening,
						reason: "opening_stock",
					});
				}
				router.replace(`/catalog/${id}`);
			}}
		/>
	);
}
