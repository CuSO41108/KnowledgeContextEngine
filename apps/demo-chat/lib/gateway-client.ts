const DEFAULT_GATEWAY_BASE_URL = "http://localhost:8080";

type QueryResponseMemory = {
  channel: string;
  type: string;
  content: string;
};

type QueryResponseResource = {
  nodeId: string;
  traceNodeId: string;
  nodePath: string;
  drilldownTrail: string[];
};

type QueryResponsePayload = {
  answer: string;
  traceId: string;
  usedContexts: {
    sessionSummary: string;
    memories: QueryResponseMemory[];
    resources: QueryResponseResource[];
  };
  compressionSummary: {
    beforeContextChars: number;
    afterContextChars: number;
  };
};

export type NormalizedQueryResponse = {
  answer: string;
  traceId: string;
  sessionSummary: string;
  memories: QueryResponseMemory[];
  resources: QueryResponseResource[];
  compressionSummary: {
    before: number;
    after: number;
  };
};

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, "");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function readString(
  container: Record<string, unknown>,
  key: string,
  options?: { allowEmpty?: boolean },
): string {
  const value = container[key];
  if (
    typeof value !== "string" ||
    (!options?.allowEmpty && value.length === 0)
  ) {
    const expected = options?.allowEmpty ? "a string" : "a non-empty string";
    throw new Error(`Expected ${key} to be ${expected}.`);
  }
  return value;
}

function readStringArray(
  container: Record<string, unknown>,
  key: string,
): string[] {
  const value = container[key];
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    throw new Error(`Expected ${key} to be a string array.`);
  }
  return value;
}

function readRequiredNumber(
  container: Record<string, unknown>,
  key: string,
): number {
  const value = container[key];
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new Error(`Expected ${key} to be a number.`);
  }
  return value;
}

export function buildGatewayUrl(base?: string): string {
  const resolvedBase =
    base ??
    process.env.GATEWAY_BASE_URL ??
    process.env.NEXT_PUBLIC_GATEWAY_BASE_URL ??
    DEFAULT_GATEWAY_BASE_URL;

  return normalizeBaseUrl(resolvedBase);
}

export function normalizeQueryResponse(
  payload: unknown,
): NormalizedQueryResponse {
  if (!isRecord(payload)) {
    throw new Error("Expected query payload to be an object.");
  }

  const usedContexts = payload.usedContexts;
  const compressionSummary = payload.compressionSummary;

  if (!isRecord(usedContexts)) {
    throw new Error("Expected usedContexts to be an object.");
  }

  if (!isRecord(compressionSummary)) {
    throw new Error("Expected compressionSummary to be an object.");
  }

  const memories = usedContexts.memories;
  if (!Array.isArray(memories)) {
    throw new Error("Expected usedContexts.memories to be an array.");
  }

  const resources = usedContexts.resources;
  if (!Array.isArray(resources)) {
    throw new Error("Expected usedContexts.resources to be an array.");
  }

  const normalizedPayload: QueryResponsePayload = {
    answer: readString(payload, "answer"),
    traceId: readString(payload, "traceId"),
    usedContexts: {
      sessionSummary: readString(usedContexts, "sessionSummary", {
        allowEmpty: true,
      }),
      memories: memories.map((memory, index) => {
        if (!isRecord(memory)) {
          throw new Error(
            `Expected usedContexts.memories[${index}] to be an object.`,
          );
        }

        return {
          channel: readString(memory, "channel"),
          type: readString(memory, "type"),
          content: readString(memory, "content"),
        };
      }),
      resources: resources.map((resource, index) => {
        if (!isRecord(resource)) {
          throw new Error(
            `Expected usedContexts.resources[${index}] to be an object.`,
          );
        }

        return {
          nodeId: readString(resource, "nodeId"),
          traceNodeId: readString(resource, "traceNodeId"),
          nodePath: readString(resource, "nodePath"),
          drilldownTrail: readStringArray(resource, "drilldownTrail"),
        };
      }),
    },
    compressionSummary: {
      beforeContextChars: readRequiredNumber(
        compressionSummary,
        "beforeContextChars",
      ),
      afterContextChars: readRequiredNumber(
        compressionSummary,
        "afterContextChars",
      ),
    },
  };

  return {
    answer: normalizedPayload.answer,
    traceId: normalizedPayload.traceId,
    sessionSummary: normalizedPayload.usedContexts.sessionSummary,
    memories: normalizedPayload.usedContexts.memories,
    resources: normalizedPayload.usedContexts.resources,
    compressionSummary: {
      before: normalizedPayload.compressionSummary.beforeContextChars,
      after: normalizedPayload.compressionSummary.afterContextChars,
    },
  };
}
