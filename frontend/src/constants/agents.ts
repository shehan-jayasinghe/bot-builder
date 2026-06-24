import type { AgentType, Industry } from "../types/agent";

export type IndustryOption = {
  value: Industry;
  label: string;
  emoji: string;
};

export type AgentTypeOption = {
  value: AgentType;
  label: string;
  description: string;
  icon: string;
  capabilities: string[];
};

export const INDUSTRIES: IndustryOption[] = [
  { value: "financial_services", label: "Financial Services", emoji: "💰" },
  { value: "logistics", label: "Logistics", emoji: "📦" },
  { value: "travel", label: "Travel", emoji: "✈️" },
  { value: "healthcare", label: "Healthcare", emoji: "🏥" },
  { value: "insurance", label: "Insurance", emoji: "🛡️" },
  { value: "other", label: "Other", emoji: "✨" },
];

export const AGENT_TYPES: AgentTypeOption[] = [
  {
    value: "payment_collections",
    label: "Payment & Collections Agent",
    description:
      "Loan repayment reminders, credit card payment reminders, overdue invoice follow-ups, payment link generation.",
    icon: "💳",
    capabilities: [
      "Send automated payment reminders",
      "Generate secure payment links",
      "Track overdue invoices",
      "Handle payment plan negotiations",
      "Escalate unresolved cases to human agents",
    ],
  },
  {
    value: "customer_onboarding",
    label: "Customer Onboarding Agent",
    description: "KYC document collection, onboarding assistance, application status updates.",
    icon: "📋",
    capabilities: [
      "Guide customers through KYC and onboarding steps",
      "Collect required documents and application details",
      "Provide application status updates",
    ],
  },
  {
    value: "customer_support_triage",
    label: "Customer Support Triage Agent",
    description: "Identify customer issues, route to correct department, resolve common queries.",
    icon: "💬",
    capabilities: [
      "Identify customer issues and route to the correct team",
      "Resolve common queries within the conversation",
      "Escalate complex cases with collected context",
    ],
  },
];

export const SAMPLE_QUESTIONS: Record<AgentType, string[]> = {
  payment_collections: [
    "What is my outstanding balance?",
    "Can I set up a payment plan?",
    "I need a payment link for my invoice",
  ],
  customer_onboarding: [
    "What documents do I need for onboarding?",
    "What is my application status?",
    "How do I complete KYC verification?",
  ],
  customer_support_triage: [
    "I have a billing issue",
    "Can you help me reset my account?",
    "I need to speak to a human agent",
  ],
};

export function getIndustryLabel(value: Industry): string {
  return INDUSTRIES.find((item) => item.value === value)?.label ?? value;
}

export function getAgentTypeOption(value: AgentType | null | undefined): AgentTypeOption | undefined {
  if (!value) {
    return undefined;
  }
  return AGENT_TYPES.find((item) => item.value === value);
}
