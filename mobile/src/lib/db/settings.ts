export type SettingKey =
	| "business_name"
	| "business_currency"
	| "business_address"
	| "business_contact"
	| "business_timezone";

export interface BusinessProfile {
	name: string;
	currency: string;
	address: string;
	contact: string;
	timezone: string;
}

const settings = new Map<SettingKey, string | null>([
	["business_name", "Tasty Meals Co."],
	["business_currency", "PHP"],
	["business_address", "123 Mabini St., Quezon City"],
	["business_contact", "+63 917 555 0123"],
	["business_timezone", "Asia/Manila"],
]);

const DEFAULT_PROFILE: BusinessProfile = {
	name: "",
	currency: "PHP",
	address: "",
	contact: "",
	timezone: "",
};

export function getSetting(key: SettingKey): string | null {
	return settings.get(key) ?? null;
}

export function setSetting(key: SettingKey, value: string | null): void {
	settings.set(key, value);
}

export function getBusinessProfile(): BusinessProfile {
	return {
		name: getSetting("business_name") ?? DEFAULT_PROFILE.name,
		currency: getSetting("business_currency") ?? DEFAULT_PROFILE.currency,
		address: getSetting("business_address") ?? DEFAULT_PROFILE.address,
		contact: getSetting("business_contact") ?? DEFAULT_PROFILE.contact,
		timezone: getSetting("business_timezone") ?? DEFAULT_PROFILE.timezone,
	};
}

export function saveBusinessProfile(p: Partial<BusinessProfile>): void {
	if (p.name !== undefined) setSetting("business_name", p.name);
	if (p.currency !== undefined) setSetting("business_currency", p.currency);
	if (p.address !== undefined) setSetting("business_address", p.address);
	if (p.contact !== undefined) setSetting("business_contact", p.contact);
	if (p.timezone !== undefined) setSetting("business_timezone", p.timezone);
}
