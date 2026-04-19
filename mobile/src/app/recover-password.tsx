import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import { useCustomToast } from "@/hooks/useCustomToast";
import { api } from "@/lib/auth";
import { emailPattern, handleError } from "@/lib/utils";
import { useRouter } from "expo-router";
import { Controller, useForm } from "react-hook-form";
import { View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

interface RecoverForm {
	email: string;
}

export default function RecoverPasswordScreen() {
	const toast = useCustomToast();
	const router = useRouter();
	const {
		control,
		handleSubmit,
		formState: { errors, isSubmitting },
	} = useForm<RecoverForm>({ defaultValues: { email: "" } });

	const onSubmit = async ({ email }: RecoverForm) => {
		try {
			await api.post(`/api/v1/password-recovery/${encodeURIComponent(email)}`);
			toast.success("Recovery email sent");
			router.replace("/login");
		} catch (err) {
			toast.error(handleError(err));
		}
	};

	return (
		<SafeAreaView className="flex-1 bg-background">
			<View className="flex-1 justify-center gap-6 px-6">
				<Text className="text-3xl font-bold">Recover Password</Text>
				<Controller
					control={control}
					name="email"
					rules={{ required: "Email is required", pattern: emailPattern }}
					render={({ field: { onChange, value } }) => (
						<FormField label="Email" error={errors.email?.message}>
							<Input
								value={value}
								onChangeText={onChange}
								placeholder="you@example.com"
								autoCapitalize="none"
								keyboardType="email-address"
							/>
						</FormField>
					)}
				/>
				<Button
					label={isSubmitting ? "Sending..." : "Send Recovery Email"}
					onPress={handleSubmit(onSubmit)}
					disabled={isSubmitting}
				/>
			</View>
		</SafeAreaView>
	);
}
