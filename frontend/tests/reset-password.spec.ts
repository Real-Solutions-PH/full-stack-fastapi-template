import { expect, test } from "@playwright/test"
import { findRecoveryLink } from "./utils/mailpit"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser, signUpNewUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

test("Password Recovery title is visible", async ({ page }) => {
  await page.goto("/recover-password")

  await expect(
    page.getByRole("heading", { name: "Password Recovery" }),
  ).toBeVisible()
})

test("Input is visible, empty and editable", async ({ page }) => {
  await page.goto("/recover-password")

  await expect(page.getByTestId("email-input")).toBeVisible()
  await expect(page.getByTestId("email-input")).toHaveText("")
  await expect(page.getByTestId("email-input")).toBeEditable()
})

test("Continue button is visible", async ({ page }) => {
  await page.goto("/recover-password")

  await expect(page.getByRole("button", { name: "Continue" })).toBeVisible()
})

test("User can reset password successfully using the link", async ({
  page,
  request,
}) => {
  const fullName = "Test User"
  const email = randomEmail()
  const password = randomPassword()
  const newPassword = randomPassword()

  // Sign up a new user
  await signUpNewUser(page, fullName, email, password)

  await page.goto("/recover-password")
  await page.getByTestId("email-input").fill(email)

  await page.getByRole("button", { name: "Continue" }).click()
  await expect(
    page.getByText("Password recovery email sent successfully"),
  ).toBeVisible()

  // Supabase (GoTrue) sends the recovery email through the local Mailpit
  // instance; the /auth/v1/verify link redirects to /reset-password?code=...
  const url = await findRecoveryLink({ request, email })

  // Set the new password and confirm it (the PKCE code verifier lives in
  // this browser context — the link must be opened in the same one).
  await page.goto(url)
  await page.waitForURL(/reset-password/)

  await page.getByTestId("new-password-input").fill(newPassword)
  await page.getByTestId("confirm-password-input").fill(newPassword)
  await page.getByRole("button", { name: "Reset Password" }).click()
  await expect(page.getByText("Password updated successfully")).toBeVisible()

  // Check if the user is able to login with the new password
  await logInUser(page, email, newPassword)
})

test("Expired or invalid reset link", async ({ page }) => {
  // No valid recovery code: the exchange fails and the form is disabled.
  await page.goto("/reset-password?code=invalid-code")

  await expect(page.getByText("Invalid or expired reset link")).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Reset Password" }),
  ).toBeDisabled()
})

test("Weak new password validation", async ({ page, request }) => {
  const fullName = "Test User"
  const email = randomEmail()
  const password = randomPassword()
  const weakPassword = "123"

  // Sign up a new user
  await signUpNewUser(page, fullName, email, password)

  await page.goto("/recover-password")
  await page.getByTestId("email-input").fill(email)
  await page.getByRole("button", { name: "Continue" }).click()
  await expect(
    page.getByText("Password recovery email sent successfully"),
  ).toBeVisible()

  const url = await findRecoveryLink({ request, email })

  // Set a weak new password
  await page.goto(url)
  await page.waitForURL(/reset-password/)
  await page.getByTestId("new-password-input").fill(weakPassword)
  await page.getByTestId("confirm-password-input").fill(weakPassword)
  await page.getByRole("button", { name: "Reset Password" }).click()

  await expect(
    page.getByText("Password must be at least 8 characters"),
  ).toBeVisible()
})
