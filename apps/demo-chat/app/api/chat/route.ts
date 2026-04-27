import {
  createUIMessageStream,
  createUIMessageStreamResponse,
} from "ai";

import { extractMessageText } from "@/lib/chat-helpers";
import type { DemoChatMessage } from "@/lib/chat-types";
import {
  resolveRouteExternalUserId,
  resolveRouteGoal,
  resolveRouteSessionId,
} from "@/lib/demo-chat-config";
import { buildGatewayUrl, normalizeQueryResponse } from "@/lib/gateway-client";

const DEFAULT_PROVIDER = "demo_local";

type ChatRequestBody = {
  externalUserId?: string;
  goal?: string;
  message?: DemoChatMessage | string;
  provider?: string;
  sessionId?: string;
};

function resolveOptionalValue(value: string | undefined, fallback: string): string {
  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : fallback;
}

async function readGatewayError(response: Response): Promise<string> {
  const errorText = await response.text();
  return errorText || response.statusText;
}

function resolveMessageText(message: ChatRequestBody["message"]): string {
  if (typeof message === "string") {
    return message.trim();
  }

  if (
    typeof message === "object" &&
    message !== null &&
    Array.isArray(message.parts)
  ) {
    return extractMessageText(message);
  }

  return "";
}

export async function POST(request: Request) {
  let body: ChatRequestBody;

  try {
    body = (await request.json()) as ChatRequestBody;
  } catch {
    return Response.json(
      { error: "Expected a JSON request body." },
      { status: 400 },
    );
  }

  const messageText = resolveMessageText(body.message);

  if (messageText.length === 0) {
    return Response.json(
      { error: "message is required." },
      { status: 400 },
    );
  }

  const sessionId = resolveRouteSessionId(body.sessionId);
  const provider = resolveOptionalValue(body.provider, DEFAULT_PROVIDER);
  const externalUserId = resolveRouteExternalUserId(body.externalUserId);
  const goal = resolveRouteGoal(body.goal);
  const gatewayBaseUrl = buildGatewayUrl();

  const sessionUrl = `${gatewayBaseUrl}/api/v1/sessions`;
  const queryUrl = `${gatewayBaseUrl}/api/v1/sessions/${encodeURIComponent(sessionId)}/query`;
  const commitUrl = `${gatewayBaseUrl}/api/v1/sessions/${encodeURIComponent(sessionId)}/commit`;
  const apiKey =
    process.env.GATEWAY_API_KEY ??
    process.env.DEMO_API_KEY ??
    process.env.NEXT_PUBLIC_DEMO_API_KEY;
  const headers = {
    "Content-Type": "application/json",
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
  };

  const sessionResponse = await fetch(sessionUrl, {
    method: "POST",
    headers,
    body: JSON.stringify({
      provider,
      externalUserId,
      sessionId,
      goal,
    }),
    cache: "no-store",
  });

  if (!sessionResponse.ok) {
    return Response.json(
      {
        error: "Gateway session creation failed.",
        details: await readGatewayError(sessionResponse),
        status: sessionResponse.status,
      },
      { status: sessionResponse.status },
    );
  }

  const gatewayResponse = await fetch(queryUrl, {
    method: "POST",
    headers,
    body: JSON.stringify({
      provider,
      externalUserId,
      message: messageText,
      goal,
    }),
    cache: "no-store",
  });

  if (!gatewayResponse.ok) {
    const errorText = await gatewayResponse.text();
    return Response.json(
      {
        error: "Gateway query failed.",
        details: errorText || gatewayResponse.statusText,
        status: gatewayResponse.status,
      },
      { status: gatewayResponse.status },
    );
  }

  const payload = normalizeQueryResponse(await gatewayResponse.json());
  const commitResponse = await fetch(commitUrl, {
    method: "POST",
    headers,
    body: JSON.stringify({
      provider,
      externalUserId,
      userMessage: messageText,
      assistantAnswer: payload.answer,
      traceId: payload.traceId,
      goal,
    }),
    cache: "no-store",
  });

  if (!commitResponse.ok) {
    return Response.json(
      {
        error: "Gateway session commit failed.",
        details: await readGatewayError(commitResponse),
        status: commitResponse.status,
      },
      { status: commitResponse.status },
    );
  }

  const stream = createUIMessageStream<DemoChatMessage>({
    execute({ writer }) {
      const textId = crypto.randomUUID();

      writer.write({
        type: "text-start",
        id: textId,
      });
      writer.write({
        type: "message-metadata",
        messageMetadata: {
          trace: payload,
        },
      });
      writer.write({
        type: "text-delta",
        id: textId,
        delta: payload.answer,
      });
      writer.write({
        type: "text-end",
        id: textId,
      });
    },
  });

  return createUIMessageStreamResponse({ stream });
}
