package com.cuso.kce.gateway;

import com.cuso.kce.gateway.api.TraceController;
import com.cuso.kce.gateway.client.EngineClient;
import com.cuso.kce.gateway.config.ApiKeyFilter;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.Map;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(TraceController.class)
@Import({ApiKeyFilter.class, TraceControllerTest.TestConfig.class})
@TestPropertySource(properties = "kce.auth.api-key=test-gateway-key")
class TraceControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private EngineClient engineClient;

    @Test
    void traceLookupReturnsProxiedTracePayload() throws Exception {
        when(engineClient.getTrace("trace-123"))
            .thenReturn(Map.of(
                "traceId", "trace-123",
                "question", "How should I reply on Zhiguang about Redis cache-aside?",
                "answer", "Reply on Zhiguang with a concise Java cache-aside explanation.",
                "usedContexts", Map.of(
                    "sessionSummary", "Draft a concise Java reply to Zhiguang.",
                    "memories", List.of(
                        Map.of("channel", "user", "type", "explanation_preference", "content", "User prefers concise Java explanations.")
                    ),
                    "resources", List.of(
                        Map.of(
                            "nodeId", "zhiguang-cache:l2:s000:000",
                            "traceNodeId", "trace-123:zhiguang-cache:l2:s000:000",
                            "nodePath", "resource://zhiguang-cache/l2/s000/000",
                            "drilldownTrail", List.of(
                                "resource://zhiguang-cache/l0/root",
                                "resource://zhiguang-cache/l1/s000",
                                "resource://zhiguang-cache/l2/s000/000"
                            )
                        )
                    )
                ),
                "compressionSummary", Map.of(
                    "beforeContextChars", 240,
                    "afterContextChars", 132
                ),
                "nodeSnapshots", List.of(
                    Map.of(
                        "nodeId", "zhiguang-cache:l2:s000:000",
                        "nodePath", "resource://zhiguang-cache/l2/s000/000",
                        "level", "l2",
                        "ancestry", List.of(
                            Map.of("node_id", "zhiguang-cache:l1:s000", "node_path", "resource://zhiguang-cache/l1/s000", "level", "l1")
                        ),
                        "snapshotContent", "Redis cache-aside keeps DB authoritative."
                    )
                )
            ));

        mockMvc.perform(get("/api/v1/traces/trace-123").header("X-API-Key", "test-gateway-key"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.traceId").value("trace-123"))
            .andExpect(jsonPath("$.usedContexts.resources[0].traceNodeId").value("trace-123:zhiguang-cache:l2:s000:000"))
            .andExpect(jsonPath("$.nodeSnapshots[0].snapshotContent").value("Redis cache-aside keeps DB authoritative."));

        verify(engineClient).getTrace("trace-123");
    }

    @Test
    void traceNodeLookupReturnsHistoricalSnapshotPayload() throws Exception {
        when(engineClient.getTraceNodeSnapshot("trace-123", "zhiguang-cache:l2:s000:000"))
            .thenReturn(Map.of(
                "nodeId", "zhiguang-cache:l2:s000:000",
                "nodePath", "resource://zhiguang-cache/l2/s000/000",
                "level", "l2",
                "ancestry", List.of(
                    Map.of("node_id", "zhiguang-cache:l1:s000", "node_path", "resource://zhiguang-cache/l1/s000", "level", "l1")
                ),
                "snapshotContent", "Historical Redis snapshot content."
            ));

        mockMvc.perform(get("/api/v1/traces/trace-123/nodes/zhiguang-cache:l2:s000:000").header("X-API-Key", "test-gateway-key"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.nodeId").value("zhiguang-cache:l2:s000:000"))
            .andExpect(jsonPath("$.snapshotContent").value("Historical Redis snapshot content."));

        verify(engineClient).getTraceNodeSnapshot("trace-123", "zhiguang-cache:l2:s000:000");
    }

    @TestConfiguration
    static class TestConfig {
        @Bean
        ApiKeyFilter apiKeyFilter() {
            return new ApiKeyFilter("test-gateway-key");
        }
    }
}
