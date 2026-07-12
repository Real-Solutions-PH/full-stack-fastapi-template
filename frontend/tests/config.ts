import path from "node:path"
import dotenv from "dotenv"

// Playwright transpiles test files to CJS, where __dirname exists natively.
// import.meta must not be used here — it forces ESM loading of the CJS
// output and crashes with "exports is not defined in ES module scope".
dotenv.config({ path: path.join(__dirname, "../../.env") })

function getEnvVar(name: string): string {
  const value = process.env[name]
  if (!value) {
    throw new Error(`Environment variable ${name} is undefined`)
  }
  return value
}

export const firstSuperuser = getEnvVar("FIRST_SUPERUSER")
export const firstSuperuserPassword = getEnvVar("FIRST_SUPERUSER_PASSWORD")
