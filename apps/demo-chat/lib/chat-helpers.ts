import type { UIMessage } from "ai";

import {
  normalizeQueryResponse,
  type NormalizedQueryResponse,
} from "./gateway-client";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

type AnyMessagePart = UIMessage["parts"][number];

function isTextPart(
  part: AnyMessagePart,
): part is Extract<AnyMessagePart, { type: "text" }> {
  return part.type === "text";
}

export function extractMessageText(message: Pick<UIMessage, "parts">): string {
  return message.parts.filter(isTextPart).map((part) => part.text).join("").trim();
}

export function normalizeTraceMetadata(
  metadata: unknown,
): NormalizedQueryResponse | null {
  if (!isRecord(metadata)) {
    return null;
  }

  const candidate = "trace" in metadata ? metadata.trace : metadata;

  if (!candidate) {
    return null;
  }

  try {
    return normalizeQueryResponse(candidate);
  } catch {
    return null;
  }
}
