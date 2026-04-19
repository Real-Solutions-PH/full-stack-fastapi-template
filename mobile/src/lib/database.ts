import { runMigrations } from "@/lib/db/migrations";
import * as SQLite from "expo-sqlite";

const DB_NAME = "app.db";

export const db = SQLite.openDatabaseSync(DB_NAME);

export function initializeDatabase(): void {
	db.execSync("PRAGMA journal_mode = WAL;");
	db.execSync("PRAGMA foreign_keys = ON;");
	runMigrations(db);
}
