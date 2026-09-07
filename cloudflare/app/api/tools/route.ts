import { desc } from "drizzle-orm";

import { getDb } from "@/db";
import { tools } from "@/db/schema";

export async function GET() {
  const db = await getDb();
  const rows = await db
    .select({
      id: tools.id,
      organizationId: tools.organizationId,
      agentId: tools.agentId,
      name: tools.name,
      executor: tools.executor,
      status: tools.status,
      createdAt: tools.createdAt,
    })
    .from(tools)
    .orderBy(desc(tools.createdAt));

  return Response.json({ tools: rows });
}

export async function POST(request: Request) {
  const body = (await request.json()) as {
    organization_id: string;
    agent_id?: string;
    name: string;
    executor: string;
    config?: string;
  };

  const db = await getDb();
  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await db.insert(tools).values({
    id,
    organizationId: body.organization_id,
    agentId: body.agent_id ?? null,
    name: body.name,
    executor: body.executor,
    config: body.config ?? null,
    status: "active",
    createdAt: now,
  });

  return Response.json({ id }, { status: 201 });
}
