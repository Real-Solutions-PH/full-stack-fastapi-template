import * as categoriesDb from "@/lib/db/categories";

export type StockStatus = "out" | "low" | "healthy";

export interface LocalProduct {
	id: string;
	name: string;
	sku: string | null;
	category_id: string | null;
	unit: string;
	current_stock: number;
	reorder_point: number;
	unit_cost: number | null;
	notes: string | null;
	archived: number;
	created_at: string;
	updated_at: string | null;
}

export interface ProductWithCategory extends LocalProduct {
	category_name: string | null;
	category_color: string | null;
}

const now = () => new Date().toISOString();

const products: LocalProduct[] = [
	{
		id: "prod-pork-belly",
		name: "Pork Belly",
		sku: "MEAT-001",
		category_id: "cat-meats",
		unit: "kg",
		current_stock: 12,
		reorder_point: 5,
		unit_cost: 320,
		notes: "Sliced, vacuum-packed",
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
	{
		id: "prod-chicken-wings",
		name: "Chicken Wings",
		sku: "POUL-001",
		category_id: "cat-poultry",
		unit: "kg",
		current_stock: 3,
		reorder_point: 5,
		unit_cost: 220,
		notes: null,
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
	{
		id: "prod-adobo-pack",
		name: "Adobo Pack",
		sku: "PANT-010",
		category_id: "cat-pantry",
		unit: "pack",
		current_stock: 0,
		reorder_point: 10,
		unit_cost: 45,
		notes: "Pre-mixed adobo seasoning",
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
	{
		id: "prod-soy-sauce",
		name: "Soy Sauce",
		sku: "PANT-001",
		category_id: "cat-pantry",
		unit: "L",
		current_stock: 18,
		reorder_point: 6,
		unit_cost: 85,
		notes: null,
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
	{
		id: "prod-vinegar",
		name: "Cane Vinegar",
		sku: "PANT-002",
		category_id: "cat-pantry",
		unit: "L",
		current_stock: 14,
		reorder_point: 5,
		unit_cost: 60,
		notes: null,
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
	{
		id: "prod-garlic",
		name: "Garlic",
		sku: "PANT-003",
		category_id: "cat-pantry",
		unit: "kg",
		current_stock: 4,
		reorder_point: 2,
		unit_cost: 180,
		notes: null,
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
	{
		id: "prod-rice",
		name: "Jasmine Rice",
		sku: "PANT-020",
		category_id: "cat-pantry",
		unit: "kg",
		current_stock: 50,
		reorder_point: 20,
		unit_cost: 65,
		notes: "25kg sack",
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
	{
		id: "prod-takeout-box",
		name: "Takeout Box (medium)",
		sku: "PACK-001",
		category_id: "cat-packaging",
		unit: "pc",
		current_stock: 240,
		reorder_point: 100,
		unit_cost: 4,
		notes: null,
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
];

function withCategory(p: LocalProduct): ProductWithCategory {
	const c = p.category_id ? categoriesDb.getCategoryById(p.category_id) : null;
	return {
		...p,
		category_name: c?.name ?? null,
		category_color: c?.color ?? null,
	};
}

export function stockStatus(
	p: Pick<LocalProduct, "current_stock" | "reorder_point">,
): StockStatus {
	if (p.current_stock <= 0) return "out";
	if (p.current_stock <= p.reorder_point) return "low";
	return "healthy";
}

export function listProducts(opts?: {
	search?: string;
	categoryId?: string | null;
	status?: StockStatus | "all";
	includeArchived?: boolean;
}): ProductWithCategory[] {
	let list = products.slice();
	if (!opts?.includeArchived) list = list.filter((p) => p.archived === 0);
	if (opts?.search) {
		const s = opts.search.toLowerCase();
		list = list.filter(
			(p) =>
				p.name.toLowerCase().includes(s) ||
				(p.sku ? p.sku.toLowerCase().includes(s) : false),
		);
	}
	if (opts?.categoryId) {
		list = list.filter((p) => p.category_id === opts.categoryId);
	}
	if (opts?.status === "out") list = list.filter((p) => p.current_stock <= 0);
	else if (opts?.status === "low")
		list = list.filter(
			(p) => p.current_stock > 0 && p.current_stock <= p.reorder_point,
		);
	else if (opts?.status === "healthy")
		list = list.filter((p) => p.current_stock > p.reorder_point);

	return list
		.sort((a, b) => a.name.localeCompare(b.name))
		.map(withCategory);
}

export function getProductById(id: string): ProductWithCategory | null {
	const p = products.find((x) => x.id === id);
	return p ? withCategory(p) : null;
}

export interface ProductInput {
	name: string;
	sku?: string | null;
	category_id?: string | null;
	unit: string;
	current_stock?: number;
	reorder_point?: number;
	unit_cost?: number | null;
	notes?: string | null;
}

export function insertProduct(id: string, input: ProductInput): void {
	products.push({
		id,
		name: input.name,
		sku: input.sku ?? null,
		category_id: input.category_id ?? null,
		unit: input.unit,
		current_stock: input.current_stock ?? 0,
		reorder_point: input.reorder_point ?? 0,
		unit_cost: input.unit_cost ?? null,
		notes: input.notes ?? null,
		archived: 0,
		created_at: now(),
		updated_at: now(),
	});
}

export function updateProduct(
	id: string,
	data: Partial<ProductInput & { archived: number; current_stock: number }>,
): void {
	const p = products.find((x) => x.id === id);
	if (!p) return;
	if (data.name !== undefined) p.name = data.name;
	if (data.sku !== undefined) p.sku = data.sku ?? null;
	if (data.category_id !== undefined) p.category_id = data.category_id ?? null;
	if (data.unit !== undefined) p.unit = data.unit;
	if (data.current_stock !== undefined) p.current_stock = data.current_stock;
	if (data.reorder_point !== undefined) p.reorder_point = data.reorder_point;
	if (data.unit_cost !== undefined) p.unit_cost = data.unit_cost ?? null;
	if (data.notes !== undefined) p.notes = data.notes ?? null;
	if (data.archived !== undefined) p.archived = data.archived;
	p.updated_at = now();
}

export function adjustStock(productId: string, delta: number): number {
	const p = products.find((x) => x.id === productId);
	if (!p) return 0;
	p.current_stock += delta;
	p.updated_at = now();
	return p.current_stock;
}

export function getProductCount(): number {
	return products.filter((p) => p.archived === 0).length;
}

export function getLowStockCount(): number {
	return products.filter(
		(p) =>
			p.archived === 0 &&
			p.current_stock > 0 &&
			p.current_stock <= p.reorder_point,
	).length;
}

export function getOutOfStockCount(): number {
	return products.filter((p) => p.archived === 0 && p.current_stock <= 0)
		.length;
}

export function getInventoryValue(): number {
	return products
		.filter((p) => p.archived === 0)
		.reduce((sum, p) => sum + p.current_stock * (p.unit_cost ?? 0), 0);
}
