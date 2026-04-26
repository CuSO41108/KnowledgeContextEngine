"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { FormEvent, useRef, useState } from "react";

import { extractMessageText, normalizeTraceMetadata } from "@/lib/chat-helpers";
import type { DemoChatMessage } from "@/lib/chat-types";
import {
  buildPreparedChatRequestBody,
  buildDemoSessionId,
  DEFAULT_GOAL,
  DEFAULT_MESSAGE,
  validatePromptInput,
} from "@/lib/demo-chat-config";
import type { NormalizedQueryResponse } from "@/lib/gateway-client";

import { TracePanel } from "@/components/trace-panel";

export function ChatShell() {
  const [sessionId, setSessionId] = useState(() => buildDemoSessionId());

  return (
    <ChatSession
      key={sessionId}
      onStartFreshSession={() => setSessionId(buildDemoSessionId())}
      sessionId={sessionId}
    />
  );
}

function ChatSession(props: {
  onStartFreshSession: () => void;
  sessionId: string;
}) {
  const [goal, setGoal] = useState(DEFAULT_GOAL);
  const [input, setInput] = useState(DEFAULT_MESSAGE);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [trace, setTrace] = useState<NormalizedQueryResponse | null>(null);
  const goalRef = useRef(goal);
  const {
    clearError,
    error,
    messages,
    setMessages,
    sendMessage,
    status,
  } = useChat<DemoChatMessage>({
    id: props.sessionId,
    onFinish: ({ message }) => {
      setTrace(normalizeTraceMetadata(message.metadata));
    },
    transport: new DefaultChatTransport({
      api: "/api/chat",
      prepareSendMessagesRequest: ({ id, messages: nextMessages }) => ({
        body: buildPreparedChatRequestBody({
          goalRef,
          messages: nextMessages,
          sessionId: id,
        }),
      }),
    }),
  });

  const isSubmitting = status === "streaming" || status === "submitted";
  const activeError = validationError ?? error?.message ?? null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    const nextValidationError = validatePromptInput(input);
    if (nextValidationError) {
      clearError();
      setTrace(null);
      setMessages([]);
      setValidationError(nextValidationError);
      return;
    }

    setValidationError(null);
    clearError();
    await sendMessage({ text: input.trim() });
  }

  return (
    <main
      style={{
        background:
          "linear-gradient(180deg, rgb(245 247 250) 0%, rgb(232 239 246) 100%)",
        minHeight: "100vh",
        padding: "32px 20px 48px",
      }}
    >
      <div
        style={{
          display: "grid",
          gap: 24,
          gridTemplateColumns: "minmax(0, 1.4fr) minmax(280px, 0.9fr)",
          margin: "0 auto",
          maxWidth: 1200,
        }}
      >
        <section
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid rgb(205 216 228)",
            borderRadius: 24,
            boxShadow: "0 18px 50px rgb(15 23 42 / 0.08)",
            padding: 24,
          }}
        >
          <div style={{ marginBottom: 20 }}>
            <p
              style={{
                color: "#385170",
                fontSize: 13,
                fontWeight: 700,
                letterSpacing: "0.08em",
                margin: 0,
                textTransform: "uppercase",
              }}
            >
              Demo Chat
            </p>
            <h1
              style={{
                color: "#10233d",
                fontSize: "clamp(2rem, 4vw, 3rem)",
                lineHeight: 1.05,
                margin: "8px 0 12px",
              }}
            >
              Zhiguang reply assistant
            </h1>
            <p
              style={{
                color: "#4c6179",
                fontSize: 16,
                lineHeight: 1.6,
                margin: 0,
              }}
            >
              Keep the UI thin: it forwards the prompt to the gateway and shows
              the live trace metadata that comes back.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            style={{ display: "grid", gap: 16, marginBottom: 24 }}
          >
            <label style={{ display: "grid", gap: 8 }}>
              <span style={{ color: "#10233d", fontWeight: 600 }}>Goal</span>
              <input
                onChange={(event) => {
                  setGoal(event.target.value);
                  goalRef.current = event.target.value;
                  if (validationError) {
                    setValidationError(null);
                  }
                }}
                style={{
                  border: "1px solid rgb(194 207 221)",
                  borderRadius: 14,
                  fontSize: 15,
                  padding: "12px 14px",
                }}
                value={goal}
              />
            </label>

            <label style={{ display: "grid", gap: 8 }}>
              <span style={{ color: "#10233d", fontWeight: 600 }}>Message</span>
              <textarea
                onChange={(event) => {
                  setInput(event.target.value);
                  if (validationError) {
                    setValidationError(null);
                  }
                }}
                rows={5}
                style={{
                  border: "1px solid rgb(194 207 221)",
                  borderRadius: 14,
                  fontFamily: "inherit",
                  fontSize: 15,
                  padding: "14px 16px",
                  resize: "vertical",
                }}
                value={input}
              />
            </label>

            <button
              disabled={isSubmitting}
              style={{
                backgroundColor: isSubmitting ? "#8aa0b8" : "#10233d",
                border: 0,
                borderRadius: 999,
                color: "#ffffff",
                cursor: isSubmitting ? "progress" : "pointer",
                fontSize: 15,
                fontWeight: 700,
                padding: "12px 18px",
                width: "fit-content",
              }}
              type="submit"
            >
              {isSubmitting ? "Querying gateway..." : "Ask demo chat"}
            </button>

            <button
              disabled={isSubmitting}
              onClick={props.onStartFreshSession}
              style={{
                backgroundColor: "#eef4fb",
                border: "1px solid rgb(194 207 221)",
                borderRadius: 999,
                color: "#18324f",
                cursor: isSubmitting ? "not-allowed" : "pointer",
                fontSize: 15,
                fontWeight: 700,
                padding: "12px 18px",
                width: "fit-content",
              }}
              type="button"
            >
              Start fresh session
            </button>
          </form>

          {activeError ? (
            <p
              style={{
                backgroundColor: "#fdecec",
                borderRadius: 14,
                color: "#9f2c2c",
                margin: "0 0 20px",
                padding: "12px 14px",
              }}
            >
              {activeError}
            </p>
          ) : null}

          <div style={{ display: "grid", gap: 14 }}>
            {messages.length === 0 ? (
              <div
                style={{
                  backgroundColor: "#f6f9fc",
                  border: "1px dashed rgb(194 207 221)",
                  borderRadius: 16,
                  color: "#5f7288",
                  padding: 18,
                }}
              >
                Submit the default Zhiguang-shaped prompt to see the answer and
                live trace panel populate.
              </div>
            ) : null}

            {messages.map((message) => {
              const text = extractMessageText(message);

              if (!text) {
                return null;
              }

              return (
                <article
                  key={message.id}
                  style={{
                    alignSelf:
                      message.role === "assistant" ? "stretch" : "flex-start",
                    backgroundColor:
                      message.role === "assistant" ? "#eef4fb" : "#10233d",
                    borderRadius: 18,
                    color: message.role === "assistant" ? "#18324f" : "#ffffff",
                    marginLeft: message.role === "assistant" ? 0 : "auto",
                    maxWidth: "min(100%, 720px)",
                    padding: "14px 16px",
                  }}
                >
                  <p
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      letterSpacing: "0.08em",
                      margin: "0 0 8px",
                      opacity: 0.72,
                      textTransform: "uppercase",
                    }}
                  >
                    {message.role}
                  </p>
                  <p
                    style={{
                      lineHeight: 1.6,
                      margin: 0,
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {text}
                  </p>
                </article>
              );
            })}
          </div>
        </section>

        <TracePanel trace={trace} />
      </div>
    </main>
  );
}
