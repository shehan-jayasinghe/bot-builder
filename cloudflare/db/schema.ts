import { sqliteTable, text } from "drizzle-orm/sqlite-core";

export const organizations = sqliteTable("organizations", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  createdAt: text("created_at").notNull(),
});

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  organizationId: text("organization_id")
    .notNull()
    .references(() => organizations.id),
  email: text("email").notNull().unique(),
  name: text("name"),
  role: text("role").notNull().default("owner"),
  passwordHash: text("password_hash"),
  createdAt: text("created_at").notNull(),
});

export const agents = sqliteTable("agents", {
  id: text("id").primaryKey(),
  organizationId: text("organization_id")
    .notNull()
    .references(() => organizations.id),
  name: text("name").notNull(),
  status: text("status").notNull().default("draft"),
  personality: text("personality"),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

export const knowledgebases = sqliteTable("knowledgebases", {
  id: text("id").primaryKey(),
  organizationId: text("organization_id")
    .notNull()
    .references(() => organizations.id),
  agentId: text("agent_id").references(() => agents.id),
  name: text("name").notNull(),
  storageType: text("storage_type").notNull().default("vector"),
  r2Key: text("r2_key"),
  status: text("status").notNull().default("pending"),
  createdAt: text("created_at").notNull(),
});

export const tools = sqliteTable("tools", {
  id: text("id").primaryKey(),
  organizationId: text("organization_id")
    .notNull()
    .references(() => organizations.id),
  agentId: text("agent_id").references(() => agents.id),
  name: text("name").notNull(),
  executor: text("executor").notNull(),
  config: text("config"),
  status: text("status").notNull().default("active"),
  createdAt: text("created_at").notNull(),
});

export const workflows = sqliteTable("workflows", {
  id: text("id").primaryKey(),
  organizationId: text("organization_id")
    .notNull()
    .references(() => organizations.id),
  agentId: text("agent_id").references(() => agents.id),
  name: text("name").notNull(),
  graph: text("graph"),
  status: text("status").notNull().default("draft"),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

export const channels = sqliteTable("channels", {
  id: text("id").primaryKey(),
  organizationId: text("organization_id")
    .notNull()
    .references(() => organizations.id),
  agentId: text("agent_id")
    .notNull()
    .references(() => agents.id),
  webhookId: text("webhook_id").notNull().unique(),
  status: text("status").notNull().default("active"),
  createdAt: text("created_at").notNull(),
});
