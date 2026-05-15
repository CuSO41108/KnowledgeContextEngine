package com.cuso.kce.gateway.client;

import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.lang.reflect.Method;
import java.net.InetSocketAddress;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import com.sun.net.httpserver.HttpServer;

import static org.assertj.core.api.Assertions.assertThat;

class EngineClientTest {

    @Test
    void resourceTreeMetadataKeepsNodeContentAsSelectionEvidence() throws Exception {
        EngineClient engineClient = new EngineClient("http://localhost:65535");
        Map<String, Object> treeResponse = Map.of(
            "nodes", List.of(
                Map.of(
                    "title", "至少一次投递与幂等 / At-least-once Delivery and Idempotency",
                    "nodePath", "resource://queue-guide/l2/s002/000",
                    "content", "Dead-letter queues help isolate poison messages, and duplicate deliveries require idempotent handlers."
                )
            )
        );

        Object metadata = ReflectionTestUtils.invokeMethod(engineClient, "buildResourceTreeMetadata", "queue-guide", treeResponse);
        Method evidenceTextsAccessor = metadata.getClass().getDeclaredMethod("evidenceTexts");
        evidenceTextsAccessor.setAccessible(true);

        @SuppressWarnings("unchecked")
        List<String> evidenceTexts = (List<String>) evidenceTextsAccessor.invoke(metadata);

        assertThat(evidenceTexts)
            .contains("queue-guide")
            .contains("至少一次投递与幂等 / At-least-once Delivery and Idempotency")
            .contains("resource://queue-guide/l2/s002/000")
            .contains("Dead-letter queues help isolate poison messages, and duplicate deliveries require idempotent handlers.");
    }

    @Test
    void zhiguangMarkdownIncludesPostMetadataAndContent() {
        EngineClient engineClient = new EngineClient("http://localhost:65535");

        String markdown = ReflectionTestUtils.invokeMethod(
            engineClient,
            "buildZhiguangPostMarkdown",
            "262804640385601536",
            "Redis cache-aside reply notes",
            "A Zhiguang note about explaining cache-aside.",
            List.of("Redis", "Java"),
            "Cache-aside keeps the database authoritative.",
            "https://zhiguang.example/posts/262804640385601536.md",
            "sha-demo",
            "42",
            "published",
            "public"
        );

        assertThat(markdown)
            .contains("# Redis cache-aside reply notes")
            .contains("Provider: zhiguang")
            .contains("Post ID: 262804640385601536")
            .contains("Tags: Redis, Java")
            .contains("## Summary")
            .contains("A Zhiguang note about explaining cache-aside.")
            .contains("## Content")
            .contains("Cache-aside keeps the database authoritative.");
    }

    @Test
    void zhiguangResourceIdUsesStableProviderScopedSlug() {
        EngineClient engineClient = new EngineClient("http://localhost:65535");

        String resourceId = ReflectionTestUtils.invokeMethod(
            engineClient,
            "buildZhiguangResourceId",
            "post_262804640385601536"
        );

        assertThat(resourceId).isEqualTo("zhiguang-post-post-262804640385601536");
    }

    @Test
    void internalTokenIsSentToEngineRequests() throws Exception {
        AtomicReference<String> authorization = new AtomicReference<>("");
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/internal/resources/test/tree", exchange -> {
            authorization.set(exchange.getRequestHeaders().getFirst("Authorization"));
            byte[] body = "{\"resourceId\":\"test\",\"nodes\":[]}".getBytes();
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, body.length);
            exchange.getResponseBody().write(body);
            exchange.close();
        });
        server.start();

        try {
            EngineClient engineClient = new EngineClient(
                "http://127.0.0.1:" + server.getAddress().getPort(),
                "test-internal-token"
            );

            engineClient.getResourceTree("test");
        } finally {
            server.stop(0);
        }

        assertThat(authorization.get()).isEqualTo("Bearer test-internal-token");
    }
}
