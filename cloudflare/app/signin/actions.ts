"use server";

import { signIn } from "@/auth";

export async function authenticate(formData: FormData) {
  await signIn("credentials", {
    email: String(formData.get("email") ?? ""),
    password: String(formData.get("password") ?? ""),
    redirectTo: "/app",
  });
}
