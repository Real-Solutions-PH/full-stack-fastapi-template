import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Text } from "@/components/ui/text";
import { useCustomToast } from "@/hooks/useCustomToast";
import { api } from "@/lib/auth";
import { confirmPasswordRules, handleError, passwordRules } from "@/lib/utils";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Controller, useForm } from "react-hook-form";
import { View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

interface ResetForm {
	new_password: string;
	confirm_password: string;
}

export default function ResetPasswordScreen() {
	const toast = useCustomToast();
	const router = useRouter();
	const { token } = useLocalSearchParams<{ token?: string }>();
	const {
		control,
		handleSubmit,
		getValues,
		formState: { errors, isSubmitting },
	} = useForm<ResetForm>({
		defaultValues: { new_password: "", confirm_password: "" },
	});

	const onSubmit = async ({ new_password }: ResetForm) => {
		if (!token) {
			toast.error("Missing reset token");
			return;
		}
		try {
			await api.post("/api/v1/reset-password", { token, new_password });
			toast.success("Password reset. Please log in.");
			router.replace("/login");
		} catch (err) {
			toast.error(handleError(err));
		}
	};

	return (
		<SafeAreaView className="flex-1 bg-background">
			<View className="flex-1 justify-center gap-6 px-6">
				<Text className="text-3xl font-bold">Reset Password</Text>

				<Controller
					control={control}
					name="new_password"
					rules={passwordRules()}
					render={({ field: { onChange, value } }) => (
						<FormField
							label="New password"
							error={errors.new_password?.message}
						>
							<Input
								value={value}
								onChangeText={onChange}
								placeholder="********"
								secureTextEntry
							/>
						</FormField>
					)}
				/>

				<Controller
					control={control}
					name="confirm_password"
					rules={confirmPasswordRules(() => getValues())}
					render={({ field: { onChange, value } }) => (
						<FormField
							label="Confirm password"
							error={errors.confirm_password?.message}
						>
							<Input
								value={value}
								onChangeText={onChange}
								placeholder="********"
								secureTextEntry
							/>
						</FormField>
					)}
				/>

				<Button
					label={isSubmitting ? "Resetting..." : "Reset Password"}
					onPress={handleSubmit(onSubmit)}
					disabled={isSubmitting}
				/>
			</View>
		</SafeAreaView>
	);
}
