import { desc } from "drizzle-orm";

import { getDb } from "@/db";
import { channels } from "@/db/schema";
import { ChannelStatus } from "@/lib/constants/channels";

export async function GET() {
  const db = await getDb();
  const rows = await db
    .select({
      id: channels.id,
      organizationId: channels.organizationId,
      agentId: channels.agentId,
      webhookId: channels.webhookId,
      status: channels.status,
      createdAt: channels.createdAt,
    })
    .from(channels)
    .orderBy(desc(channels.createdAt));

  return Response.json({ channels: rows });
}

export async function POST(request: Request) {
  const body = (await request.json()) as {
    organization_id: string;
    agent_id: string;
  };

  const db = await getDb();
  const id = crypto.randomUUID();
  const webhookId = crypto.randomUUID();
  const now = new Date().toISOString();

  await db.insert(channels).values({
    id,
    organizationId: body.organization_id,
    agentId: body.agent_id,
    webhookId,
    status: ChannelStatus.Active,
    createdAt: now,
  });

  return Response.json({ id, webhook_id: webhookId }, { status: 201 });
}
