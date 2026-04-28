import { OfflineBanner } from "@/components/offline-banner";
import { Tabs } from "expo-router";
import { View } from "react-native";

export default function AppLayout() {
	return (
		<View className="flex-1">
			<OfflineBanner />
			<Tabs screenOptions={{ headerShown: true }}>
				<Tabs.Screen name="index" options={{ title: "Home" }} />
				<Tabs.Screen
					name="catalog"
					options={{ title: "Catalog", headerShown: false }}
				/>
				<Tabs.Screen
					name="recipes"
					options={{ title: "Cook", headerShown: false }}
				/>
				<Tabs.Screen name="reports" options={{ title: "Reports" }} />
				<Tabs.Screen name="settings" options={{ title: "Settings" }} />
				<Tabs.Screen name="movements" options={{ href: null }} />
				<Tabs.Screen name="items" options={{ href: null }} />
				<Tabs.Screen
					name="categories"
					options={{ href: null, title: "Categories" }}
				/>
				<Tabs.Screen
					name="business-profile"
					options={{ href: null, title: "Business profile" }}
				/>
				<Tabs.Screen
					name="export"
					options={{ href: null, title: "Export data" }}
				/>
			</Tabs>
		</View>
	);
}
