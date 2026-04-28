import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import { Link, useRouter } from "expo-router";
import { KeyboardAvoidingView, Platform, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function LoginScreen() {
	const router = useRouter();

	return (
		<SafeAreaView className="flex-1 bg-background">
			<KeyboardAvoidingView
				behavior={Platform.OS === "ios" ? "padding" : undefined}
				className="flex-1 justify-center px-6"
			>
				<View className="gap-6">
					<Text className="text-3xl font-bold">Log In</Text>

					<FormField label="Email">
						<Input
							placeholder="you@example.com"
							autoCapitalize="none"
							keyboardType="email-address"
						/>
					</FormField>

					<FormField label="Password">
						<Input placeholder="********" secureTextEntry />
					</FormField>

					<Button label="Log In" onPress={() => router.replace("/")} />

					<View className="flex-row justify-between">
						<Link href="/signup">
							<Text className="text-sm text-primary">Sign up</Text>
						</Link>
						<Link href="/recover-password">
							<Text className="text-sm text-primary">Forgot password?</Text>
						</Link>
					</View>
				</View>
			</KeyboardAvoidingView>
		</SafeAreaView>
	);
}
