type NoopDb = Record<string, (...args: unknown[]) => unknown>;

const noop = () => undefined;
const empty = () => [];

export const db = {
	execSync: noop,
	runSync: () => ({ lastInsertRowId: 0, changes: 0 }),
	getFirstSync: () => null,
	getAllSync: empty,
	getEachSync: empty,
	prepareSync: () => ({ executeSync: noop, finalizeSync: noop }),
	closeSync: noop,
	execAsync: async () => undefined,
	runAsync: async () => ({ lastInsertRowId: 0, changes: 0 }),
	getFirstAsync: async () => null,
	getAllAsync: async () => [],
	getEachAsync: empty,
	withTransactionAsync: async (cb: () => Promise<void>) => cb(),
	withExclusiveTransactionAsync: async (cb: () => Promise<void>) => cb(),
} as unknown as NoopDb;

export function initializeDatabase(): void {}
