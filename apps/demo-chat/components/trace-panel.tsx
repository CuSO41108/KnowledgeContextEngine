import type { ReactNode } from "react";

import type { NormalizedQueryResponse } from "@/lib/gateway-client";

type TracePanelProps = {
  trace: NormalizedQueryResponse | null;
};

function PanelSection(props: {
  children: ReactNode;
  title: string;
}) {
  return (
    <section style={{ display: "grid", gap: 10 }}>
      <h2
        style={{
          color: "#10233d",
          fontSize: 16,
          margin: 0,
        }}
      >
        {props.title}
      </h2>
      {props.children}
    </section>
  );
}

function ItemCard(props: { children: ReactNode }) {
  return (
    <div
      style={{
        backgroundColor: "#f7f9fc",
        border: "1px solid rgb(215 224 234)",
        borderRadius: 16,
        padding: 14,
      }}
    >
      {props.children}
    </div>
  );
}

export function TracePanel({ trace }: TracePanelProps) {
  return (
    <aside
      style={{
        alignSelf: "start",
        backgroundColor: "#ffffff",
        border: "1px solid rgb(205 216 228)",
        borderRadius: 24,
        boxShadow: "0 18px 50px rgb(15 23 42 / 0.08)",
        display: "grid",
        gap: 20,
        padding: 24,
      }}
    >
      <div>
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
          Live Trace
        </p>
        <h1
          style={{
            color: "#10233d",
            fontSize: 28,
            lineHeight: 1.1,
            margin: "8px 0 10px",
          }}
        >
          Gateway metadata
        </h1>
        <p
          style={{
            color: "#5f7288",
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          This panel only renders normalized data returned by{" "}
          <code>/api/chat</code>.
        </p>
      </div>

      {!trace ? (
        <div
          style={{
            backgroundColor: "#f6f9fc",
            border: "1px dashed rgb(194 207 221)",
            borderRadius: 16,
            color: "#5f7288",
            padding: 16,
          }}
        >
          No trace yet. Submit a Zhiguang reply request to inspect the live
          session summary, memory hits, retrieved resources, and compression
          stats.
        </div>
      ) : (
        <>
          <PanelSection title="Trace ID">
            <ItemCard>
              <code
                style={{
                  color: "#18324f",
                  display: "block",
                  fontSize: 13,
                  overflowWrap: "anywhere",
                }}
              >
                {trace.traceId}
              </code>
            </ItemCard>
          </PanelSection>

          <PanelSection title="Session Summary">
            <ItemCard>
              <p style={{ color: "#18324f", lineHeight: 1.6, margin: 0 }}>
                {trace.sessionSummary}
              </p>
            </ItemCard>
          </PanelSection>

          <PanelSection title="Memories">
            <div style={{ display: "grid", gap: 12 }}>
              {trace.memories.map((memory, index) => (
                <ItemCard key={`${memory.channel}-${memory.type}-${index}`}>
                  <p
                    style={{
                      color: "#385170",
                      fontSize: 12,
                      fontWeight: 700,
                      letterSpacing: "0.06em",
                      margin: "0 0 8px",
                      textTransform: "uppercase",
                    }}
                  >
                    {memory.channel} / {memory.type}
                  </p>
                  <p style={{ color: "#18324f", lineHeight: 1.6, margin: 0 }}>
                    {memory.content}
                  </p>
                </ItemCard>
              ))}
            </div>
          </PanelSection>

          <PanelSection title="Resources">
            <div style={{ display: "grid", gap: 12 }}>
              {trace.resources.map((resource) => (
                <ItemCard key={resource.traceNodeId}>
                  <p style={{ color: "#10233d", fontWeight: 700, margin: "0 0 8px" }}>
                    {resource.nodeId}
                  </p>
                  <p style={{ color: "#385170", margin: "0 0 10px" }}>
                    traceNodeId: <code>{resource.traceNodeId}</code>
                  </p>
                  <p style={{ color: "#18324f", margin: "0 0 10px" }}>
                    <code style={{ overflowWrap: "anywhere" }}>
                      {resource.nodePath}
                    </code>
                  </p>
                  <ol
                    style={{
                      color: "#5f7288",
                      margin: 0,
                      paddingInlineStart: 18,
                    }}
                  >
                    {resource.drilldownTrail.map((path) => (
                      <li key={path} style={{ marginBottom: 6, overflowWrap: "anywhere" }}>
                        <code>{path}</code>
                      </li>
                    ))}
                  </ol>
                </ItemCard>
              ))}
            </div>
          </PanelSection>

          <PanelSection title="Compression">
            <ItemCard>
              <p style={{ color: "#18324f", margin: "0 0 8px" }}>
                Before context chars: <strong>{trace.compressionSummary.before}</strong>
              </p>
              <p style={{ color: "#18324f", margin: 0 }}>
                After context chars: <strong>{trace.compressionSummary.after}</strong>
              </p>
            </ItemCard>
          </PanelSection>
        </>
      )}
    </aside>
  );
}
