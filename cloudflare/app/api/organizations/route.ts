import { getDb } from "@/db";
import { organizations } from "@/db/schema";

export async function POST(request: Request) {
  const body = (await request.json()) as { name: string };

  const db = await getDb();
  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await db.insert(organizations).values({
    id,
    name: body.name,
    createdAt: now,
  });

  return Response.json({ id }, { status: 201 });
}
