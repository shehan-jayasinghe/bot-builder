export function getApiError(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const detail = (error as { response?: { data?: { detail?: string | { msg?: string }[] } } }).response?.data
      ?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail) && detail[0]?.msg) {
      return detail[0].msg;
    }
    return "Request failed.";
  }
  return "Request failed.";
}
