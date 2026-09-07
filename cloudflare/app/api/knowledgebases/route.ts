import { desc } from "drizzle-orm";

import { getDb } from "@/db";
import { knowledgebases } from "@/db/schema";

export async function GET() {
  const db = await getDb();
  const rows = await db
    .select({
      id: knowledgebases.id,
      organizationId: knowledgebases.organizationId,
      agentId: knowledgebases.agentId,
      name: knowledgebases.name,
      storageType: knowledgebases.storageType,
      r2Key: knowledgebases.r2Key,
      status: knowledgebases.status,
      createdAt: knowledgebases.createdAt,
    })
    .from(knowledgebases)
    .orderBy(desc(knowledgebases.createdAt));

  return Response.json({ knowledgebases: rows });
}

export async function POST(request: Request) {
  const body = (await request.json()) as {
    organization_id: string;
    agent_id?: string;
    name: string;
    storage_type?: "vector" | "keyword";
  };

  const storageType = body.storage_type ?? "vector";
  if (storageType !== "vector" && storageType !== "keyword") {
    return Response.json({ error: "storage_type must be vector or keyword" }, { status: 400 });
  }

  const db = await getDb();
  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await db.insert(knowledgebases).values({
    id,
    organizationId: body.organization_id,
    agentId: body.agent_id ?? null,
    name: body.name,
    storageType,
    status: "pending",
    createdAt: now,
  });

  return Response.json({ id }, { status: 201 });
}
