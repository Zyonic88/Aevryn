const MIN_PASSWORD_LENGTH = 12;

export type LoginFormValues = {
  email: string;
  password: string;
};

export type RegisterFormValues = LoginFormValues & {
  displayName: string;
};

export type PasswordRecoveryFormValues = {
  email: string;
};

export type PasswordUpdateFormValues = {
  password: string;
  confirmPassword: string;
};

export type LoginPayloadValues = {
  email: string;
  password: string;
};

export type RegisterPayloadValues = LoginPayloadValues & {
  userId: string;
  displayName: string;
};

export type PasswordRecoveryPayloadValues = {
  email: string;
};

export type PasswordUpdatePayloadValues = {
  password: string;
};

export function buildLoginPayload(values: LoginFormValues): LoginPayloadValues {
  const email = normalizeEmail(values.email);
  if (!isLikelyEmail(email)) {
    throw new Error("Enter a valid email address.");
  }
  if (!values.password) {
    throw new Error("Password is required.");
  }
  return { email, password: values.password };
}

export function buildRegisterPayload(values: RegisterFormValues): RegisterPayloadValues {
  const login = buildLoginPayload(values);
  const displayName = normalizeDisplayName(values.displayName);
  if (!displayName) {
    throw new Error("Display name is required.");
  }
  validateNewPassword(login.password);
  return {
    ...login,
    userId: userIdFromEmail(login.email),
    displayName,
  };
}

export function buildPasswordRecoveryPayload(
  values: PasswordRecoveryFormValues,
): PasswordRecoveryPayloadValues {
  const email = normalizeEmail(values.email);
  if (!isLikelyEmail(email)) {
    throw new Error("Enter a valid email address.");
  }
  return { email };
}

export function buildPasswordUpdatePayload(
  values: PasswordUpdateFormValues,
): PasswordUpdatePayloadValues {
  validateNewPassword(values.password);
  if (values.password !== values.confirmPassword) {
    throw new Error("Passwords do not match.");
  }
  return { password: values.password };
}

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function normalizeDisplayName(displayName: string): string {
  return displayName.trim().replace(/\s+/g, " ");
}

export function isLikelyEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function validateNewPassword(password: string): void {
  if (password.length < MIN_PASSWORD_LENGTH) {
    throw new Error("Password must be at least 12 characters.");
  }
  if (password.trim() !== password) {
    throw new Error("Password cannot start or end with whitespace.");
  }
  if (!/[a-z]/.test(password)) {
    throw new Error("Password must include a lowercase letter.");
  }
  if (!/[A-Z]/.test(password)) {
    throw new Error("Password must include an uppercase letter.");
  }
  if (!/\d/.test(password)) {
    throw new Error("Password must include a number.");
  }
}

function userIdFromEmail(email: string): string {
  const localPart = email.split("@")[0] ?? "user";
  const normalized = localPart
    .toLowerCase()
    .replace(/[^a-z0-9_]/g, "_")
    .replace(/_+/g, "_");
  const trimmed = normalized.replace(/^_+|_+$/g, "");
  return `user_${trimmed || "account"}`;
}
