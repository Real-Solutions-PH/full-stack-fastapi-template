export interface LocalCategory {
	id: string;
	name: string;
	color: string | null;
	archived: number;
	created_at: string;
}

const now = () => new Date().toISOString();

const categories: LocalCategory[] = [
	{
		id: "cat-meats",
		name: "Meats",
		color: "#ef4444",
		archived: 0,
		created_at: now(),
	},
	{
		id: "cat-poultry",
		name: "Poultry",
		color: "#eab308",
		archived: 0,
		created_at: now(),
	},
	{
		id: "cat-pantry",
		name: "Pantry",
		color: "#22c55e",
		archived: 0,
		created_at: now(),
	},
	{
		id: "cat-packaging",
		name: "Packaging",
		color: "#3b82f6",
		archived: 0,
		created_at: now(),
	},
];

export function listCategories(includeArchived = false): LocalCategory[] {
	const list = includeArchived
		? categories
		: categories.filter((c) => c.archived === 0);
	return [...list].sort((a, b) => a.name.localeCompare(b.name));
}

export function getCategoryById(id: string): LocalCategory | null {
	return categories.find((c) => c.id === id) ?? null;
}

export function insertCategory(c: {
	id: string;
	name: string;
	color?: string | null;
}): void {
	categories.push({
		id: c.id,
		name: c.name,
		color: c.color ?? null,
		archived: 0,
		created_at: now(),
	});
}

export function updateCategory(
	id: string,
	data: Partial<Pick<LocalCategory, "name" | "color" | "archived">>,
): void {
	const c = categories.find((x) => x.id === id);
	if (!c) return;
	if (data.name !== undefined) c.name = data.name;
	if (data.color !== undefined) c.color = data.color;
	if (data.archived !== undefined) c.archived = data.archived;
}

export function deleteCategory(id: string): void {
	const idx = categories.findIndex((c) => c.id === id);
	if (idx >= 0) categories.splice(idx, 1);
}
