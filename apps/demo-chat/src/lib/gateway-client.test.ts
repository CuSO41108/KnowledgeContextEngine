import { afterEach, describe, expect, it } from "vitest";

import {
  buildGatewayUrl,
  normalizeQueryResponse,
} from "../../lib/gateway-client";

const ORIGINAL_GATEWAY_BASE_URL = process.env.GATEWAY_BASE_URL;
const ORIGINAL_PUBLIC_GATEWAY_BASE_URL =
  process.env.NEXT_PUBLIC_GATEWAY_BASE_URL;

afterEach(() => {
  if (ORIGINAL_GATEWAY_BASE_URL === undefined) {
    delete process.env.GATEWAY_BASE_URL;
  } else {
    process.env.GATEWAY_BASE_URL = ORIGINAL_GATEWAY_BASE_URL;
  }

  if (ORIGINAL_PUBLIC_GATEWAY_BASE_URL === undefined) {
    delete process.env.NEXT_PUBLIC_GATEWAY_BASE_URL;
  } else {
    process.env.NEXT_PUBLIC_GATEWAY_BASE_URL =
      ORIGINAL_PUBLIC_GATEWAY_BASE_URL;
  }
});

describe("buildGatewayUrl", () => {
  it("prefers explicit and env gateway urls before localhost", () => {
    process.env.GATEWAY_BASE_URL = "http://gateway-java:8080/";
    process.env.NEXT_PUBLIC_GATEWAY_BASE_URL =
      "http://browser-visible-gateway:8080/";

    expect(buildGatewayUrl(" http://manual-gateway:8080/ ")).toBe(
      "http://manual-gateway:8080",
    );
    expect(buildGatewayUrl()).toBe("http://gateway-java:8080");

    delete process.env.GATEWAY_BASE_URL;

    expect(buildGatewayUrl()).toBe("http://browser-visible-gateway:8080");

    delete process.env.NEXT_PUBLIC_GATEWAY_BASE_URL;

    expect(buildGatewayUrl()).toBe("http://localhost:8080");
  });
});

describe("normalizeQueryResponse", () => {
  it("normalizes answer, trace, resource, memory, and compression fields", () => {
    const normalized = normalizeQueryResponse({
      answer: "Zhiguang reply draft",
      traceId: "trace-demo-001",
      usedContexts: {
        resources: [
          {
            nodeId: "node-l2",
            traceNodeId: "trace-node-l2",
            nodePath: "resource://zhiguang-java-cache-playbook/l2/redis/000",
            drilldownTrail: [
              "resource://zhiguang-java-cache-playbook/l0/root",
              "resource://zhiguang-java-cache-playbook/l1/redis",
              "resource://zhiguang-java-cache-playbook/l2/redis/000",
            ],
          },
        ],
        memories: [
          {
            channel: "user",
            type: "explanation_preference",
            content: "User prefers concise Java explanations.",
          },
          {
            channel: "task_experience",
            type: "successful_resource",
            content:
              "Helpful resource: resource://zhiguang-java-cache-playbook/l2/redis/000",
          },
        ],
        sessionSummary: "Goal=reply on Zhiguang",
      },
      compressionSummary: { beforeContextChars: 12, afterContextChars: 8 },
    });

    expect(normalized.answer).toBe("Zhiguang reply draft");
    expect(normalized.traceId).toBe("trace-demo-001");
    expect(normalized.resources[0].traceNodeId).toBe("trace-node-l2");
    expect(normalized.resources[0].nodePath).toBe(
      "resource://zhiguang-java-cache-playbook/l2/redis/000",
    );
    expect(normalized.resources[0].drilldownTrail[1]).toBe(
      "resource://zhiguang-java-cache-playbook/l1/redis",
    );
    expect(normalized.memories[1].channel).toBe("task_experience");
    expect(normalized.memories[1].content).toContain("Helpful resource");
    expect(normalized.sessionSummary).toBe("Goal=reply on Zhiguang");
    expect(normalized.compressionSummary).toEqual({ before: 12, after: 8 });
  });
});
