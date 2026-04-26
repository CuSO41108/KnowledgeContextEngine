import {
  createUIMessageStream,
  createUIMessageStreamResponse,
} from "ai";

import { extractMessageText } from "@/lib/chat-helpers";
import type { DemoChatMessage } from "@/lib/chat-types";
import { resolveRouteGoal, resolveRouteSessionId } from "@/lib/demo-chat-config";
import { buildGatewayUrl, normalizeQueryResponse } from "@/lib/gateway-client";

const DEFAULT_EXTERNAL_USER_ID = "demo-user-1";
const DEFAULT_PROVIDER = "demo_local";

type ChatRequestBody = {
  externalUserId?: string;
  goal?: string;
  message?: DemoChatMessage | string;
  provider?: string;
  sessionId?: string;
};

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

  const gatewayUrl = `${buildGatewayUrl()}/api/v1/sessions/${encodeURIComponent(sessionId)}/query`;
  const apiKey =
    process.env.GATEWAY_API_KEY ??
    process.env.DEMO_API_KEY ??
    process.env.NEXT_PUBLIC_DEMO_API_KEY;

  const gatewayResponse = await fetch(gatewayUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { "X-API-Key": apiKey } : {}),
    },
    body: JSON.stringify({
      provider:
        typeof body.provider === "string" && body.provider.trim().length > 0
          ? body.provider.trim()
          : DEFAULT_PROVIDER,
      externalUserId:
        typeof body.externalUserId === "string" &&
        body.externalUserId.trim().length > 0
          ? body.externalUserId.trim()
          : DEFAULT_EXTERNAL_USER_ID,
      message: messageText,
      goal: resolveRouteGoal(body.goal),
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
