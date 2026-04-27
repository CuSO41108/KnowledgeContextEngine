import type { DemoChatMessage } from "@/lib/chat-types";

export const DEFAULT_GOAL = "write a Zhiguang reply about Redis cache-aside";
export const DEFAULT_MESSAGE =
  "I am replying on Zhiguang. How should I explain Redis cache-aside briefly?";
export const FALLBACK_EXTERNAL_USER_ID = "demo-user-1";
export const FALLBACK_SESSION_ID = "demo-session";

function buildFallbackToken() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function defaultIdFactory() {
  if (
    typeof globalThis.crypto !== "undefined" &&
    typeof globalThis.crypto.randomUUID === "function"
  ) {
    return globalThis.crypto.randomUUID();
  }

  return buildFallbackToken();
}

export function buildDemoSessionId(
  createId: () => string = defaultIdFactory,
) {
  const suffix = createId().trim() || buildFallbackToken();
  return `${FALLBACK_SESSION_ID}-${suffix}`;
}

export function buildDemoExternalUserId(
  createId: () => string = defaultIdFactory,
) {
  const suffix = createId().trim() || buildFallbackToken();
  return `demo-user-${suffix}`;
}

export function resolveSubmittedGoal(goal: string) {
  return goal.trim();
}

export function resolveRouteGoal(goal: unknown) {
  if (typeof goal === "string") {
    return goal.trim();
  }

  return DEFAULT_GOAL;
}

export function resolveRouteSessionId(sessionId: unknown) {
  if (typeof sessionId === "string" && sessionId.trim().length > 0) {
    return sessionId.trim();
  }

  return FALLBACK_SESSION_ID;
}

export function resolveRouteExternalUserId(externalUserId: unknown) {
  if (typeof externalUserId === "string") {
    return externalUserId.trim();
  }

  return FALLBACK_EXTERNAL_USER_ID;
}

export function validatePromptInput(message: string) {
  if (message.trim().length === 0) {
    return "Please enter the Zhiguang reply prompt.";
  }

  return null;
}

export function buildPreparedChatRequestBody(props: {
  externalUserId: string;
  goalRef: { current: string };
  messages: DemoChatMessage[];
  sessionId: string;
}) {
  return {
    externalUserId: props.externalUserId.trim(),
    goal: resolveSubmittedGoal(props.goalRef.current),
    message: props.messages.at(-1),
    sessionId: props.sessionId,
  };
}
