import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "../auth/ProtectedRoute";
import { PublicAuthRoute } from "../auth/PublicAuthRoute";
import { AppShell } from "../layouts/AppShell";
import { AddKnowledgeBasePage } from "../pages/agent/AddKnowledgeBasePage";
import { AddToolPage } from "../pages/agent/AddToolPage";
import { AgentPage } from "../pages/agent/AgentPage";
import { AgentDetailPage } from "../pages/agent/AgentDetailPage";
import { CreateAgentPage } from "../pages/agent/CreateAgentPage";
import { SignInPage } from "../pages/auth/SignInPage";
import { SignUpPage } from "../pages/auth/SignUpPage";
import { VerifyEmailPage } from "../pages/auth/VerifyEmailPage";
import { AnalyticsPage } from "../pages/analytics/AnalyticsPage";
import { ChannelsPage } from "../pages/channels/ChannelsPage";
import { ConversationsPage } from "../pages/conversations/ConversationsPage";
import { DataSourcesPage } from "../pages/data-sources/DataSourcesPage";
import { HomePage } from "../pages/home/HomePage";
import { SchedulersPage } from "../pages/schedulers/SchedulersPage";
import { SettingsPage } from "../pages/settings/SettingsPage";
import { WorkflowsPage } from "../pages/workflows/WorkflowsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/verify-email" element={<VerifyEmailPage />} />

      <Route element={<PublicAuthRoute />}>
        <Route path="/sign-in" element={<SignInPage />} />
        <Route path="/sign-up" element={<SignUpPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="agent" element={<AgentPage />} />
          <Route path="agent/new" element={<CreateAgentPage />} />
          <Route path="agent/:agentId/knowledgebases/new" element={<AddKnowledgeBasePage />} />
          <Route path="agent/:agentId/tools/new" element={<AddToolPage />} />
          <Route path="agent/:agentId" element={<AgentDetailPage />} />
          <Route path="workflows" element={<WorkflowsPage />} />
          <Route path="data-sources" element={<DataSourcesPage />} />
          <Route path="channels" element={<ChannelsPage />} />
          <Route path="conversations" element={<ConversationsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="schedulers" element={<SchedulersPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
