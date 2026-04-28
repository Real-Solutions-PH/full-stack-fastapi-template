import * as productsDb from "@/lib/db/products";

export type MovementType = "in" | "out" | "adjustment" | "batch_cook";

export interface LocalMovement {
	id: string;
	client_uuid: string;
	product_id: string;
	movement_type: MovementType;
	quantity: number;
	reason: string | null;
	balance_after: number;
	unit_cost: number | null;
	notes: string | null;
	created_at: string;
}

export interface MovementWithProduct extends LocalMovement {
	product_name: string;
	product_unit: string;
}

export interface RecordMovementInput {
	product_id: string;
	movement_type: MovementType;
	quantity: number;
	reason?: string | null;
	unit_cost?: number | null;
	notes?: string | null;
	client_uuid?: string;
}

export class InsufficientStockError extends Error {
	constructor(
		public available: number,
		public requested: number,
	) {
		super(`Insufficient stock: ${available} available, ${requested} requested`);
		this.name = "InsufficientStockError";
	}
}

const sqliteTimestamp = (d = new Date()): string =>
	`${d.toISOString().slice(0, 19).replace("T", " ")}`;

function uuid() {
	if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
		return crypto.randomUUID();
	}
	return `mov-${Math.random().toString(36).slice(2, 10)}`;
}

const movements: LocalMovement[] = [
	{
		id: "mv-seed-1",
		client_uuid: "mv-seed-1",
		product_id: "prod-pork-belly",
		movement_type: "in",
		quantity: 10,
		reason: "delivery",
		balance_after: 12,
		unit_cost: 320,
		notes: "Monday delivery",
		created_at: sqliteTimestamp(new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)),
	},
	{
		id: "mv-seed-2",
		client_uuid: "mv-seed-2",
		product_id: "prod-chicken-wings",
		movement_type: "out",
		quantity: -4,
		reason: "production",
		balance_after: 3,
		unit_cost: null,
		notes: null,
		created_at: sqliteTimestamp(new Date(Date.now() - 6 * 60 * 60 * 1000)),
	},
	{
		id: "mv-seed-3",
		client_uuid: "mv-seed-3",
		product_id: "prod-adobo-pack",
		movement_type: "out",
		quantity: -2,
		reason: "spoilage",
		balance_after: 0,
		unit_cost: 45,
		notes: "Past expiry",
		created_at: sqliteTimestamp(new Date(Date.now() - 24 * 60 * 60 * 1000)),
	},
	{
		id: "mv-seed-4",
		client_uuid: "mv-seed-4",
		product_id: "prod-rice",
		movement_type: "in",
		quantity: 25,
		reason: "delivery",
		balance_after: 50,
		unit_cost: 65,
		notes: null,
		created_at: sqliteTimestamp(new Date(Date.now() - 12 * 60 * 60 * 1000)),
	},
	{
		id: "mv-seed-5",
		client_uuid: "mv-seed-5",
		product_id: "prod-soy-sauce",
		movement_type: "adjustment",
		quantity: 0,
		reason: "recount",
		balance_after: 18,
		unit_cost: null,
		notes: "Quarterly recount",
		created_at: sqliteTimestamp(new Date(Date.now() - 3 * 60 * 60 * 1000)),
	},
];

export function recordMovement(input: RecordMovementInput): LocalMovement {
	const product = productsDb.getProductById(input.product_id);
	if (!product) throw new Error("Product not found");

	const clientUuid = input.client_uuid ?? uuid();
	const existing = movements.find((m) => m.client_uuid === clientUuid);
	if (existing) return existing;

	let delta: number;
	let newBalance: number;
	switch (input.movement_type) {
		case "in":
			delta = Math.abs(input.quantity);
			newBalance = product.current_stock + delta;
			break;
		case "out":
		case "batch_cook": {
			const out = Math.abs(input.quantity);
			if (product.current_stock < out) {
				throw new InsufficientStockError(product.current_stock, out);
			}
			delta = -out;
			newBalance = product.current_stock - out;
			break;
		}
		case "adjustment":
			newBalance = input.quantity;
			delta = newBalance - product.current_stock;
			break;
	}

	productsDb.adjustStock(input.product_id, delta);

	const entry: LocalMovement = {
		id: uuid(),
		client_uuid: clientUuid,
		product_id: input.product_id,
		movement_type: input.movement_type,
		quantity: delta,
		reason: input.reason ?? null,
		balance_after: newBalance,
		unit_cost: input.unit_cost ?? null,
		notes: input.notes ?? null,
		created_at: sqliteTimestamp(),
	};
	movements.unshift(entry);
	return entry;
}

export function listMovements(opts?: {
	productId?: string;
	type?: MovementType;
	limit?: number;
	sinceDays?: number;
}): MovementWithProduct[] {
	let list = movements.slice();
	if (opts?.productId) list = list.filter((m) => m.product_id === opts.productId);
	if (opts?.type) list = list.filter((m) => m.movement_type === opts.type);
	if (opts?.sinceDays) {
		const cutoff = Date.now() - opts.sinceDays * 24 * 60 * 60 * 1000;
		list = list.filter(
			(m) => new Date(`${m.created_at.replace(" ", "T")}Z`).getTime() >= cutoff,
		);
	}
	list.sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
	const limit = opts?.limit ?? 200;
	return list.slice(0, limit).map((m) => {
		const p = productsDb.getProductById(m.product_id);
		return {
			...m,
			product_name: p?.name ?? "Unknown",
			product_unit: p?.unit ?? "",
		};
	});
}

export function getTodayMovementCount(): number {
	const start = new Date();
	start.setHours(0, 0, 0, 0);
	return movements.filter(
		(m) =>
			new Date(`${m.created_at.replace(" ", "T")}Z`).getTime() >= start.getTime(),
	).length;
}
