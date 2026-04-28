import * as movementsDb from "@/lib/db/movements";
import * as productsDb from "@/lib/db/products";

export interface LocalRecipe {
	id: string;
	name: string;
	yield_qty: number | null;
	yield_unit: string | null;
	notes: string | null;
	archived: number;
	created_at: string;
	updated_at: string | null;
}

export interface RecipeItem {
	recipe_id: string;
	product_id: string;
	quantity: number;
}

export interface RecipeItemDetailed extends RecipeItem {
	product_name: string;
	product_unit: string;
	current_stock: number;
}

export interface RecipeWithCount extends LocalRecipe {
	item_count: number;
}

export interface ProductionRun {
	id: string;
	recipe_id: string;
	recipe_name: string;
	multiplier: number;
	notes: string | null;
	created_at: string;
}

const now = () => new Date().toISOString();

function uuid() {
	if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
		return crypto.randomUUID();
	}
	return `rcp-${Math.random().toString(36).slice(2, 10)}`;
}

const recipes: LocalRecipe[] = [
	{
		id: "rec-chicken-adobo",
		name: "Chicken Adobo",
		yield_qty: 6,
		yield_unit: "portions",
		notes: "Classic family recipe.",
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
	{
		id: "rec-pork-sinigang",
		name: "Pork Sinigang",
		yield_qty: 8,
		yield_unit: "portions",
		notes: null,
		archived: 0,
		created_at: now(),
		updated_at: null,
	},
];

const recipeItems: RecipeItem[] = [
	{ recipe_id: "rec-chicken-adobo", product_id: "prod-chicken-wings", quantity: 1 },
	{ recipe_id: "rec-chicken-adobo", product_id: "prod-soy-sauce", quantity: 0.25 },
	{ recipe_id: "rec-chicken-adobo", product_id: "prod-vinegar", quantity: 0.25 },
	{ recipe_id: "rec-chicken-adobo", product_id: "prod-garlic", quantity: 0.05 },
	{ recipe_id: "rec-pork-sinigang", product_id: "prod-pork-belly", quantity: 1.5 },
	{ recipe_id: "rec-pork-sinigang", product_id: "prod-garlic", quantity: 0.03 },
];

const productionRuns: ProductionRun[] = [];

export function listRecipes(includeArchived = false): RecipeWithCount[] {
	const list = includeArchived
		? recipes.slice()
		: recipes.filter((r) => r.archived === 0);
	return list
		.sort((a, b) => a.name.localeCompare(b.name))
		.map((r) => ({
			...r,
			item_count: recipeItems.filter((i) => i.recipe_id === r.id).length,
		}));
}

export function getRecipeById(id: string): LocalRecipe | null {
	return recipes.find((r) => r.id === id) ?? null;
}

export function getRecipeItems(recipeId: string): RecipeItemDetailed[] {
	const items = recipeItems.filter((i) => i.recipe_id === recipeId);
	return items
		.map((i) => {
			const p = productsDb.getProductById(i.product_id);
			return {
				...i,
				product_name: p?.name ?? "Unknown",
				product_unit: p?.unit ?? "",
				current_stock: p?.current_stock ?? 0,
			};
		})
		.sort((a, b) => a.product_name.localeCompare(b.product_name));
}

export interface RecipeInput {
	name: string;
	yield_qty?: number | null;
	yield_unit?: string | null;
	notes?: string | null;
}

export function insertRecipe(id: string, input: RecipeInput): void {
	recipes.push({
		id,
		name: input.name,
		yield_qty: input.yield_qty ?? null,
		yield_unit: input.yield_unit ?? null,
		notes: input.notes ?? null,
		archived: 0,
		created_at: now(),
		updated_at: now(),
	});
}

export function updateRecipe(
	id: string,
	data: Partial<RecipeInput & { archived: number }>,
): void {
	const r = recipes.find((x) => x.id === id);
	if (!r) return;
	if (data.name !== undefined) r.name = data.name;
	if (data.yield_qty !== undefined) r.yield_qty = data.yield_qty ?? null;
	if (data.yield_unit !== undefined) r.yield_unit = data.yield_unit ?? null;
	if (data.notes !== undefined) r.notes = data.notes ?? null;
	if (data.archived !== undefined) r.archived = data.archived;
	r.updated_at = now();
}

export function setRecipeItems(
	recipeId: string,
	items: { product_id: string; quantity: number }[],
): void {
	for (let i = recipeItems.length - 1; i >= 0; i--) {
		if (recipeItems[i].recipe_id === recipeId) recipeItems.splice(i, 1);
	}
	for (const it of items) {
		recipeItems.push({
			recipe_id: recipeId,
			product_id: it.product_id,
			quantity: it.quantity,
		});
	}
}

export function deleteRecipe(id: string): void {
	for (let i = recipeItems.length - 1; i >= 0; i--) {
		if (recipeItems[i].recipe_id === id) recipeItems.splice(i, 1);
	}
	const idx = recipes.findIndex((r) => r.id === id);
	if (idx >= 0) recipes.splice(idx, 1);
}

export interface PreCookCheck {
	ok: boolean;
	items: {
		product_id: string;
		product_name: string;
		product_unit: string;
		required: number;
		available: number;
		short: number;
	}[];
}

export function preCookCheck(
	recipeId: string,
	multiplier: number,
): PreCookCheck {
	const items = getRecipeItems(recipeId);
	const result = items.map((it) => {
		const required = it.quantity * multiplier;
		const available = it.current_stock;
		const short = Math.max(0, required - available);
		return {
			product_id: it.product_id,
			product_name: it.product_name,
			product_unit: it.product_unit,
			required,
			available,
			short,
		};
	});
	return { ok: result.every((r) => r.short === 0), items: result };
}

export function executeBatchCook(
	recipeId: string,
	multiplier: number,
	notes?: string | null,
): ProductionRun {
	const recipe = getRecipeById(recipeId);
	if (!recipe) throw new Error("Recipe not found");
	const check = preCookCheck(recipeId, multiplier);
	if (!check.ok) {
		const shorts = check.items
			.filter((i) => i.short > 0)
			.map((i) => `${i.product_name} (short ${i.short} ${i.product_unit})`)
			.join(", ");
		throw new Error(`Insufficient stock: ${shorts}`);
	}
	const runId = uuid();
	const run: ProductionRun = {
		id: runId,
		recipe_id: recipeId,
		recipe_name: recipe.name,
		multiplier,
		notes: notes ?? null,
		created_at: now(),
	};
	productionRuns.unshift(run);
	for (const it of check.items) {
		movementsDb.recordMovement({
			product_id: it.product_id,
			movement_type: "batch_cook",
			quantity: it.required,
			reason: "batch_cook",
			notes: `${recipe.name} ×${multiplier} · run ${runId.slice(0, 8)}`,
		});
	}
	return run;
}

export function listProductionRuns(limit = 50): ProductionRun[] {
	return productionRuns.slice(0, limit);
}

export function getRecipeCount(): number {
	return recipes.filter((r) => r.archived === 0).length;
}
