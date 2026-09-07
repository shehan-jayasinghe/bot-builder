import { eq } from "drizzle-orm";

import { getDb } from "@/db";
import { agents } from "@/db/schema";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ agentId: string }> },
) {
  const { agentId } = await params;
  const db = await getDb();
  const agent = await db.select().from(agents).where(eq(agents.id, agentId)).get();

  if (!agent) {
    return Response.json({ error: "Agent not found" }, { status: 404 });
  }

  return Response.json({ agent });
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ agentId: string }> },
) {
  const { agentId } = await params;
  const body = (await request.json()) as {
    name?: string;
    status?: string;
    personality?: string;
  };

  const db = await getDb();
  await db
    .update(agents)
    .set({
      ...(body.name !== undefined ? { name: body.name } : {}),
      ...(body.status !== undefined ? { status: body.status } : {}),
      ...(body.personality !== undefined ? { personality: body.personality } : {}),
      updatedAt: new Date().toISOString(),
    })
    .where(eq(agents.id, agentId));

  return Response.json({ id: agentId });
}
