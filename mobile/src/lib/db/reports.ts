import * as movementsDb from "@/lib/db/movements";
import * as productsDb from "@/lib/db/products";

export interface MovementSummary {
	total_in: number;
	total_out: number;
	movement_count: number;
}

export interface CategoryValueRow {
	category_id: string | null;
	category_name: string | null;
	product_count: number;
	total_value: number;
}

export interface WasteReportRow {
	product_id: string;
	product_name: string;
	product_unit: string;
	quantity_lost: number;
	cost_lost: number;
}

export interface TopProductRow {
	product_id: string;
	product_name: string;
	product_unit: string;
	total_consumed: number;
}

function parseSqliteTimestamp(s: string): number {
	return new Date(`${s.replace(" ", "T")}Z`).getTime();
}

function inRange(created_at: string, from?: string, to?: string): boolean {
	const t = parseSqliteTimestamp(created_at);
	if (from && t < parseSqliteTimestamp(from)) return false;
	if (to && t >= parseSqliteTimestamp(to)) return false;
	return true;
}

export function movementSummary(from?: string, to?: string): MovementSummary {
	const all = movementsDb.listMovements({ limit: 10_000 });
	const filtered = all.filter((m) => inRange(m.created_at, from, to));
	let total_in = 0;
	let total_out = 0;
	for (const m of filtered) {
		if (m.quantity > 0) total_in += m.quantity;
		else total_out += -m.quantity;
	}
	return { total_in, total_out, movement_count: filtered.length };
}

export function valueByCategory(): CategoryValueRow[] {
	const products = productsDb.listProducts();
	const groups = new Map<string, CategoryValueRow>();
	for (const p of products) {
		const key = p.category_id ?? "__uncat__";
		const existing = groups.get(key) ?? {
			category_id: p.category_id,
			category_name: p.category_name,
			product_count: 0,
			total_value: 0,
		};
		existing.product_count += 1;
		existing.total_value += p.current_stock * (p.unit_cost ?? 0);
		groups.set(key, existing);
	}
	return [...groups.values()].sort((a, b) => b.total_value - a.total_value);
}

export function wasteReport(from?: string, to?: string): WasteReportRow[] {
	const all = movementsDb.listMovements({ limit: 10_000 });
	const filtered = all.filter(
		(m) =>
			(m.reason === "spoilage" || m.reason === "damaged") &&
			inRange(m.created_at, from, to),
	);
	const groups = new Map<string, WasteReportRow>();
	for (const m of filtered) {
		const product = productsDb.getProductById(m.product_id);
		const key = m.product_id;
		const lostQty = -m.quantity;
		const lostCost = lostQty * (product?.unit_cost ?? 0);
		const existing = groups.get(key) ?? {
			product_id: m.product_id,
			product_name: m.product_name,
			product_unit: m.product_unit,
			quantity_lost: 0,
			cost_lost: 0,
		};
		existing.quantity_lost += lostQty;
		existing.cost_lost += lostCost;
		groups.set(key, existing);
	}
	return [...groups.values()].sort((a, b) => b.cost_lost - a.cost_lost);
}

export function topConsumed(
	from?: string,
	to?: string,
	limit = 10,
): TopProductRow[] {
	const all = movementsDb.listMovements({ limit: 10_000 });
	const filtered = all.filter(
		(m) => m.quantity < 0 && inRange(m.created_at, from, to),
	);
	const groups = new Map<string, TopProductRow>();
	for (const m of filtered) {
		const key = m.product_id;
		const existing = groups.get(key) ?? {
			product_id: m.product_id,
			product_name: m.product_name,
			product_unit: m.product_unit,
			total_consumed: 0,
		};
		existing.total_consumed += -m.quantity;
		groups.set(key, existing);
	}
	return [...groups.values()]
		.sort((a, b) => b.total_consumed - a.total_consumed)
		.slice(0, limit);
}
