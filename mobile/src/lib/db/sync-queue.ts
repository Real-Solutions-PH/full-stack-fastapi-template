export interface SyncEntry {
	id: number;
	entity_type: string;
	entity_id: string;
	action: "create" | "update" | "delete";
	payload: string | null;
	created_at: string;
	retry_count: number;
}

export function enqueueSync(_entry: {
	entity_type: string;
	entity_id: string;
	action: "create" | "update" | "delete";
	payload: string | null;
}): void {}

export function getPendingSyncEntries(): SyncEntry[] {
	return [];
}

export function removeSyncEntry(_id: number): void {}

export function incrementRetryCount(_id: number): void {}

export function getSyncQueueCount(): number {
	return 0;
}

export function clearSyncQueue(): void {}
