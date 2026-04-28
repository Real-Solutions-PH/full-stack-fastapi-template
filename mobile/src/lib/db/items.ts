export interface LocalItem {
	id: string;
	title: string;
	description: string | null;
	owner_id: string;
	created_at: string | null;
	updated_at: string | null;
	is_local: number;
}

const items: LocalItem[] = [
	{
		id: "item-1",
		title: "Sample item",
		description: "Demo entry — frontend walkthrough only.",
		owner_id: "demo-user",
		created_at: new Date().toISOString(),
		updated_at: null,
		is_local: 0,
	},
];

export function getLocalItems(): LocalItem[] {
	return items
		.slice()
		.sort((a, b) => (a.created_at && b.created_at ? (a.created_at < b.created_at ? 1 : -1) : 0));
}

export function getLocalItemById(id: string): LocalItem | null {
	return items.find((i) => i.id === id) ?? null;
}

export function insertItem(item: LocalItem): void {
	const idx = items.findIndex((i) => i.id === item.id);
	if (idx >= 0) items[idx] = item;
	else items.unshift(item);
}

export function updateItem(
	id: string,
	data: Partial<Pick<LocalItem, "title" | "description" | "is_local">>,
): void {
	const it = items.find((x) => x.id === id);
	if (!it) return;
	if (data.title !== undefined) it.title = data.title;
	if (data.description !== undefined) it.description = data.description;
	if (data.is_local !== undefined) it.is_local = data.is_local;
	it.updated_at = new Date().toISOString();
}

export function deleteItem(id: string): void {
	const idx = items.findIndex((i) => i.id === id);
	if (idx >= 0) items.splice(idx, 1);
}

export function upsertItemsFromServer(
	incoming: Array<{
		id: string;
		title: string;
		description?: string | null;
		owner_id: string;
		created_at?: string | null;
	}>,
): void {
	for (const item of incoming) {
		const idx = items.findIndex((i) => i.id === item.id);
		const next: LocalItem = {
			id: item.id,
			title: item.title,
			description: item.description ?? null,
			owner_id: item.owner_id,
			created_at: item.created_at ?? null,
			updated_at: null,
			is_local: 0,
		};
		if (idx >= 0) items[idx] = next;
		else items.push(next);
	}
}

export function getLocalItemCount(): number {
	return items.length;
}

export function clearItems(): void {
	items.length = 0;
}
