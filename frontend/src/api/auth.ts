import { api } from "./client";

export type Organization = {
  id: string;
  name: string;
  industry?: string | null;
  status: string;
};

export type User = {
  id: string;
  clerk_id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  user_type: string;
  is_root: boolean;
  organization_id: string;
  status: string;
};

export type MeResponse = {
  user: User;
  organization: Organization;
};

export type RegisterRequest = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  organization_name: string;
  industry?: string;
};

export type RegisterResponse = MeResponse & {
  email_verified: boolean;
  verification_sent: boolean;
  verification_id?: string | null;
};

export type ResendVerificationResponse = {
  message: string;
  verification_sent: boolean;
  verification_id?: string | null;
};

export type VerifyEmailResponse = {
  message: string;
  email_verified: boolean;
};

export async function getMe(): Promise<MeResponse> {
  const { data } = await api.get<MeResponse>("/auth/me");
  return data;
}

export async function registerUser(payload: RegisterRequest): Promise<RegisterResponse> {
  const { data } = await api.post<RegisterResponse>("/auth/register", payload);
  return data;
}

export async function resendVerificationEmail(email: string): Promise<ResendVerificationResponse> {
  const { data } = await api.post<ResendVerificationResponse>("/auth/resend-verification", { email });
  return data;
}

export async function verifyEmailCode(
  email: string,
  code: string,
  verificationId: string,
): Promise<VerifyEmailResponse> {
  const { data } = await api.post<VerifyEmailResponse>("/auth/verify-email", {
    email,
    code,
    verification_id: verificationId,
  });
  return data;
}
