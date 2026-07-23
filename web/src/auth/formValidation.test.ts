import { describe, expect, it } from "vitest";

import {
  buildLoginPayload,
  buildPasswordRecoveryPayload,
  buildPasswordUpdatePayload,
  buildRegisterPayload,
  normalizeDisplayName,
  normalizeEmail,
  validateNewPassword,
} from "./formValidation";

describe("auth form validation", () => {
  it("normalizes email and display name values", () => {
    expect(normalizeEmail("  DEMO@Example.COM  ")).toBe("demo@example.com");
    expect(normalizeDisplayName("  Demo    User  ")).toBe("Demo User");
  });

  it("builds login payloads with normalized email", () => {
    expect(buildLoginPayload({ email: "  DEMO@Example.COM ", password: "secret" })).toEqual({
      email: "demo@example.com",
      password: "secret",
    });
  });

  it("rejects invalid login email and blank passwords", () => {
    expect(() => buildLoginPayload({ email: "demo", password: "secret" })).toThrow(
      "Enter a valid email address.",
    );
    expect(() => buildLoginPayload({ email: "demo@example.com", password: "" })).toThrow(
      "Password is required.",
    );
  });

  it("builds register payloads with deterministic user IDs", () => {
    expect(
      buildRegisterPayload({
        displayName: "  Demo   User ",
        email: "Demo.User@example.com",
        password: "StrongPass123",
      }),
    ).toEqual({
      userId: "user_demo_user",
      displayName: "Demo User",
      email: "demo.user@example.com",
      password: "StrongPass123",
    });
  });

  it("rejects weak new passwords", () => {
    expect(() => validateNewPassword("Short1")).toThrow("at least 12");
    expect(() => validateNewPassword("lowercase1234")).toThrow("uppercase");
    expect(() => validateNewPassword("NoNumberPass")).toThrow("number");
    expect(() => validateNewPassword(" StrongPass123 ")).toThrow("whitespace");
  });

  it("builds password recovery payloads with normalized email", () => {
    expect(buildPasswordRecoveryPayload({ email: "  DEMO@Example.COM  " })).toEqual({
      email: "demo@example.com",
    });
    expect(() => buildPasswordRecoveryPayload({ email: "demo" })).toThrow(
      "Enter a valid email address.",
    );
  });

  it("builds password update payloads only when confirmation matches", () => {
    expect(
      buildPasswordUpdatePayload({
        password: "FreshPassword123",
        confirmPassword: "FreshPassword123",
      }),
    ).toEqual({ password: "FreshPassword123" });
    expect(() =>
      buildPasswordUpdatePayload({
        password: "FreshPassword123",
        confirmPassword: "DifferentPassword123",
      }),
    ).toThrow("Passwords do not match.");
  });
});
