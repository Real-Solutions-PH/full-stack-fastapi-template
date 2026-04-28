function escapeCsv(v: unknown): string {
	if (v === null || v === undefined) return "";
	const s = String(v);
	if (s.includes(",") || s.includes('"') || s.includes("\n")) {
		return `"${s.replace(/"/g, '""')}"`;
	}
	return s;
}

export function toCsv(
	headers: string[],
	rows: (string | number | null | undefined)[][],
): string {
	const lines: string[] = [];
	lines.push(headers.map(escapeCsv).join(","));
	for (const row of rows) {
		lines.push(row.map(escapeCsv).join(","));
	}
	return lines.join("\n");
}
