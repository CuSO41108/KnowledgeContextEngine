package com.cuso.kce.gateway;

import com.cuso.kce.gateway.api.SessionController;
import com.cuso.kce.gateway.client.EngineClient;
import com.cuso.kce.gateway.config.ApiKeyFilter;
import com.cuso.kce.gateway.identity.IdentityService;
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

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(SessionController.class)
@Import({ApiKeyFilter.class, SessionControllerTest.TestConfig.class})
@TestPropertySource(properties = "kce.auth.api-key=test-gateway-key")
class SessionControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private IdentityService identityService;

    @MockBean
    private EngineClient engineClient;

    @Test
    void sessionQueryReturnsGatewayProxyPayload() throws Exception {
        when(identityService.resolveInternalUserId("wechat", "zhiguang-001"))
            .thenReturn("0f8fad5b-d9cb-469f-a165-70867728950e");
        when(engineClient.query(
            anyString(),
            anyString(),
            anyString(),
            anyString(),
            anyString()
        )).thenReturn(
            Map.of(
                "answer", "Reply on Zhiguang with a concise Java cache-aside explanation.",
                "traceId", "trace-123",
                "usedContexts", Map.of(
                    "sessionSummary", "Draft a concise Java reply to Zhiguang.",
                    "memories", List.of(
                        Map.of("channel", "user", "type", "explanation_preference", "content", "User prefers concise Java explanations."),
                        Map.of("channel", "task_experience", "type", "successful_resource", "content", "Helpful resource: resource://zhiguang-cache/l2/s000/000")
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
                )
            )
        );

        mockMvc.perform(
                post("/api/v1/sessions/session-1/query")
                    .header("X-API-Key", "test-gateway-key")
                    .contentType(APPLICATION_JSON)
                    .content("""
                        {
                          "provider": "wechat",
                          "externalUserId": "zhiguang-001",
                          "message": "How should I reply on Zhiguang about Redis cache-aside?",
                          "goal": "Draft a concise Java answer."
                        }
                        """)
            )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.traceId").value("trace-123"))
            .andExpect(jsonPath("$.answer").value("Reply on Zhiguang with a concise Java cache-aside explanation."))
            .andExpect(jsonPath("$.usedContexts.resources[0].traceNodeId").value("trace-123:zhiguang-cache:l2:s000:000"))
            .andExpect(jsonPath("$.usedContexts.memories[1].channel").value("task_experience"))
            .andExpect(jsonPath("$.compressionSummary.beforeContextChars").value(240));

        verify(identityService).resolveInternalUserId("wechat", "zhiguang-001");
        verify(engineClient).query(
            "session-1",
            "0f8fad5b-d9cb-469f-a165-70867728950e",
            "wechat",
            "How should I reply on Zhiguang about Redis cache-aside?",
            "Draft a concise Java answer."
        );
    }

    @TestConfiguration
    static class TestConfig {
        @Bean
        ApiKeyFilter apiKeyFilter() {
            return new ApiKeyFilter("test-gateway-key");
        }
    }
}
