import { getDb } from "@/db";
import { users } from "@/db/schema";
import { UserRole } from "@/lib/constants/users";
import { hashPassword } from "@/lib/password";

const roles = new Set<string>(Object.values(UserRole));

export async function POST(request: Request) {
  const body = (await request.json()) as {
    organization_id: string;
    email: string;
    name?: string;
    role?: string;
    password: string;
  };

  const role = body.role ?? UserRole.Owner;
  if (!roles.has(role)) {
    return Response.json({ error: "Invalid role" }, { status: 400 });
  }

  const db = await getDb();
  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await db.insert(users).values({
    id,
    organizationId: body.organization_id,
    email: body.email,
    name: body.name ?? null,
    role,
    passwordHash: await hashPassword(body.password),
    createdAt: now,
  });

  return Response.json({ id }, { status: 201 });
}
