import { desc } from "drizzle-orm";

import { getDb } from "@/db";
import { workflows } from "@/db/schema";
import { WorkflowStatus } from "@/lib/constants/workflows";

export async function GET() {
  const db = await getDb();
  const rows = await db
    .select({
      id: workflows.id,
      organizationId: workflows.organizationId,
      agentId: workflows.agentId,
      name: workflows.name,
      status: workflows.status,
      createdAt: workflows.createdAt,
      updatedAt: workflows.updatedAt,
    })
    .from(workflows)
    .orderBy(desc(workflows.createdAt));

  return Response.json({ workflows: rows });
}

export async function POST(request: Request) {
  const body = (await request.json()) as {
    organization_id: string;
    agent_id?: string;
    name: string;
    graph?: string;
  };

  const db = await getDb();
  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await db.insert(workflows).values({
    id,
    organizationId: body.organization_id,
    agentId: body.agent_id ?? null,
    name: body.name,
    graph: body.graph ?? null,
    status: WorkflowStatus.Draft,
    createdAt: now,
    updatedAt: now,
  });

  return Response.json({ id }, { status: 201 });
}
