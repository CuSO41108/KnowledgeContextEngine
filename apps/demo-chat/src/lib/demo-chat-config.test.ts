import { describe, expect, it } from "vitest";

import {
  buildPreparedChatRequestBody,
  buildDemoExternalUserId,
  buildDemoSessionId,
  resolveRouteGoal,
  resolveRouteExternalUserId,
  resolveRouteSessionId,
  resolveSubmittedGoal,
  validatePromptInput,
} from "../../lib/demo-chat-config";

describe("demo-chat-config", () => {
  it("builds a fresh demo session id with a stable prefix", () => {
    expect(buildDemoSessionId(() => "trace-test-001")).toBe(
      "demo-session-trace-test-001",
    );
  });

  it("builds a fresh external user id with a stable prefix", () => {
    expect(buildDemoExternalUserId(() => "trace-test-001")).toBe(
      "demo-user-trace-test-001",
    );
  });

  it("keeps an intentionally blank submitted goal blank", () => {
    expect(resolveSubmittedGoal("   ")).toBe("");
  });

  it("only falls back to the default goal when the route receives no goal", () => {
    expect(resolveRouteGoal(undefined)).toBe(
      "write a Zhiguang reply about Redis cache-aside",
    );
    expect(resolveRouteGoal("   ")).toBe("");
  });

  it("uses the fallback session id only when the route receives none", () => {
    expect(resolveRouteSessionId(" demo-session-test ")).toBe(
      "demo-session-test",
    );
    expect(resolveRouteSessionId(undefined)).toBe("demo-session");
  });

  it("uses the fallback external user id only when the route receives none", () => {
    expect(resolveRouteExternalUserId(" demo-user-test ")).toBe(
      "demo-user-test",
    );
    expect(resolveRouteExternalUserId(undefined)).toBe("demo-user-1");
  });

  it("validates that the prompt message is not blank", () => {
    expect(validatePromptInput("   ")).toBe(
      "Please enter the Zhiguang reply prompt.",
    );
    expect(validatePromptInput("hello")).toBeNull();
  });

  it("builds a chat request body from the latest goal ref value", () => {
    const goalRef = { current: "  trimmed goal  " };

    expect(
      buildPreparedChatRequestBody({
        externalUserId: " demo-user-test ",
        goalRef,
        messages: [
          {
            id: "msg-1",
            parts: [{ type: "text", text: "hello" }],
            role: "user",
          },
        ],
        sessionId: "demo-session-test",
      }),
    ).toEqual({
      externalUserId: "demo-user-test",
      goal: "trimmed goal",
      message: {
        id: "msg-1",
        parts: [{ type: "text", text: "hello" }],
        role: "user",
      },
      sessionId: "demo-session-test",
    });
  });
});
