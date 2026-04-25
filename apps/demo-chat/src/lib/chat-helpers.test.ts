import { describe, expect, it } from "vitest";

import {
  extractMessageText,
  normalizeTraceMetadata,
} from "../../lib/chat-helpers";

describe("extractMessageText", () => {
  it("joins text parts and ignores non-text parts", () => {
    const text = extractMessageText({
      parts: [
        { type: "text", text: "Explain Redis " },
        { type: "step-start" },
        { type: "text", text: "cache-aside briefly." },
      ],
    });

    expect(text).toBe("Explain Redis cache-aside briefly.");
  });
});

describe("normalizeTraceMetadata", () => {
  it("reads the normalized trace payload from message metadata", () => {
    const trace = normalizeTraceMetadata({
      trace: {
        answer: "Use Redis cache-aside for hot reads.",
        traceId: "trace-demo-002",
        usedContexts: {
          resources: [
            {
              nodeId: "node-l2",
              traceNodeId: "trace-node-l2",
              nodePath: "resource://zhiguang-redis/l2/cache-aside/000",
              drilldownTrail: [
                "resource://zhiguang-redis/l0/root",
                "resource://zhiguang-redis/l1/cache-patterns",
                "resource://zhiguang-redis/l2/cache-aside/000",
              ],
            },
          ],
          memories: [
            {
              channel: "user",
              type: "tone",
              content: "Prefer concise Zhiguang replies.",
            },
          ],
          sessionSummary: "Goal=reply on Zhiguang",
        },
        compressionSummary: {
          beforeContextChars: 120,
          afterContextChars: 84,
        },
      },
    });

    expect(trace).not.toBeNull();
    expect(trace?.traceId).toBe("trace-demo-002");
    expect(trace?.resources[0].drilldownTrail[2]).toBe(
      "resource://zhiguang-redis/l2/cache-aside/000",
    );
    expect(trace?.compressionSummary).toEqual({ before: 120, after: 84 });
  });
});
