import { and, eq } from "drizzle-orm";

import { getDb } from "@/db";
import { channels } from "@/db/schema";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ webhookId: string }> },
) {
  const { webhookId } = await params;
  const body = (await request.json()) as {
    sender_id: string;
    message: string;
  };

  const db = await getDb();
  const channel = await db
    .select()
    .from(channels)
    .where(and(eq(channels.webhookId, webhookId), eq(channels.status, "active")))
    .get();

  if (!channel) {
    return Response.json({ error: "Channel not found" }, { status: 404 });
  }

  return Response.json({
    agent_id: channel.agentId,
    sender_id: body.sender_id,
    text: "Chat runtime not wired yet",
  });
}
