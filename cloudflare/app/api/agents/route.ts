import { desc } from "drizzle-orm";

import { getDb } from "@/db";
import { agents } from "@/db/schema";

export async function GET() {
  const db = await getDb();
  const rows = await db
    .select({
      id: agents.id,
      organizationId: agents.organizationId,
      name: agents.name,
      status: agents.status,
      createdAt: agents.createdAt,
    })
    .from(agents)
    .orderBy(desc(agents.createdAt));

  return Response.json({ agents: rows });
}

export async function POST(request: Request) {
  const body = (await request.json()) as {
    organization_id: string;
    name: string;
    personality?: string;
  };

  const db = await getDb();
  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await db.insert(agents).values({
    id,
    organizationId: body.organization_id,
    name: body.name,
    status: "draft",
    personality: body.personality ?? null,
    createdAt: now,
    updatedAt: now,
  });

  return Response.json({ id }, { status: 201 });
}
