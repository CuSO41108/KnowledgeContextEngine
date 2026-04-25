import { describe, expect, it } from "vitest";

import {
  buildPreparedChatRequestBody,
  buildDemoSessionId,
  resolveRouteGoal,
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
