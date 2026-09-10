"use server";

import { signIn } from "@/auth";
import { getDb } from "@/db";
import { organizations, users } from "@/db/schema";
import { UserRole } from "@/lib/constants/users";
import { hashPassword } from "@/lib/password";

export async function createAccount(formData: FormData) {
  const organizationName = String(formData.get("organization_name") ?? "").trim();
  const name = String(formData.get("name") ?? "").trim();
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  const db = await getDb();
  const now = new Date().toISOString();
  const organizationId = crypto.randomUUID();

  await db.insert(organizations).values({
    id: organizationId,
    name: organizationName,
    createdAt: now,
  });

  await db.insert(users).values({
    id: crypto.randomUUID(),
    organizationId,
    email,
    name,
    role: UserRole.Owner,
    passwordHash: await hashPassword(password),
    createdAt: now,
  });

  await signIn("credentials", {
    email,
    password,
    redirectTo: "/",
  });
}
