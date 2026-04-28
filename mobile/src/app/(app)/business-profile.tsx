import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import * as settingsDb from "@/lib/db/settings";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Alert, ScrollView, View } from "react-native";

const COMMON_CURRENCIES = ["PHP", "USD", "EUR", "JPY", "SGD", "AUD"] as const;

export default function BusinessProfileScreen() {
	const router = useRouter();
	const initial = settingsDb.getBusinessProfile();
	const [name, setName] = useState(initial.name);
	const [currency, setCurrency] = useState(initial.currency);
	const [address, setAddress] = useState(initial.address);
	const [contact, setContact] = useState(initial.contact);
	const [timezone, setTimezone] = useState(initial.timezone);

	const handleSave = () => {
		settingsDb.saveBusinessProfile({
			name: name.trim(),
			currency: currency.trim().toUpperCase(),
			address: address.trim(),
			contact: contact.trim(),
			timezone: timezone.trim(),
		});
		Alert.alert("Saved", "Business profile updated.");
		router.back();
	};

	return (
		<ScrollView
			className="flex-1 bg-background"
			contentContainerClassName="p-4 gap-4"
		>
			<View className="gap-1.5">
				<Text className="text-sm font-medium">Business name</Text>
				<Input
					value={name}
					onChangeText={setName}
					placeholder="e.g., Tasty Meals Co."
				/>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Currency</Text>
				<View className="flex-row flex-wrap gap-2">
					{COMMON_CURRENCIES.map((c) => (
						<Button
							key={c}
							size="sm"
							variant={currency === c ? "default" : "outline"}
							label={c}
							onPress={() => setCurrency(c)}
						/>
					))}
				</View>
				<Input
					value={currency}
					onChangeText={setCurrency}
					placeholder="3-letter code"
					autoCapitalize="characters"
					maxLength={6}
				/>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Address</Text>
				<Input
					value={address}
					onChangeText={setAddress}
					placeholder="optional"
				/>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Contact</Text>
				<Input
					value={contact}
					onChangeText={setContact}
					placeholder="phone or email"
				/>
			</View>

			<View className="gap-1.5">
				<Text className="text-sm font-medium">Timezone</Text>
				<Input
					value={timezone}
					onChangeText={setTimezone}
					placeholder="e.g., Asia/Manila"
					autoCapitalize="none"
				/>
			</View>

			<View className="mt-2 flex-row gap-2">
				<Button
					variant="outline"
					label="Cancel"
					onPress={() => router.back()}
					className="flex-1"
				/>
				<Button label="Save" onPress={handleSave} className="flex-1" />
			</View>
		</ScrollView>
	);
}
