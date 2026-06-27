const STORAGE_PREFIX = "bot-builder-preview-session";

function storageKey(agentId: string): string {
  return `${STORAGE_PREFIX}:${agentId}`;
}

function randomSuffix(): string {
  return Math.random().toString(36).slice(2, 10);
}

export function getOrCreatePreviewSenderId(agentId: string): string {
  const key = storageKey(agentId);
  const existing = localStorage.getItem(key);
  if (existing) {
    return existing;
  }
  const senderId = `preview-session-${randomSuffix()}`;
  localStorage.setItem(key, senderId);
  return senderId;
}

export function clearPreviewSenderId(agentId: string): string {
  const senderId = `preview-session-${randomSuffix()}`;
  localStorage.setItem(storageKey(agentId), senderId);
  return senderId;
}
