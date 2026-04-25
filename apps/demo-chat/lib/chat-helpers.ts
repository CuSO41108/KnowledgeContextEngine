import type { UIMessage } from "ai";

import {
  normalizeQueryResponse,
  type NormalizedQueryResponse,
} from "./gateway-client";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isNormalizedTraceCandidate(
  value: unknown,
): value is NormalizedQueryResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.answer === "string" &&
    typeof value.traceId === "string" &&
    typeof value.sessionSummary === "string" &&
    Array.isArray(value.memories) &&
    Array.isArray(value.resources) &&
    isRecord(value.compressionSummary) &&
    typeof value.compressionSummary.before === "number" &&
    typeof value.compressionSummary.after === "number"
  );
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
    if (isNormalizedTraceCandidate(candidate)) {
      return normalizeQueryResponse({
        answer: candidate.answer,
        traceId: candidate.traceId,
        usedContexts: {
          sessionSummary: candidate.sessionSummary,
          memories: candidate.memories,
          resources: candidate.resources,
        },
        compressionSummary: {
          beforeContextChars: candidate.compressionSummary.before,
          afterContextChars: candidate.compressionSummary.after,
        },
      });
    }

    return normalizeQueryResponse(candidate);
  } catch {
    return null;
  }
}
