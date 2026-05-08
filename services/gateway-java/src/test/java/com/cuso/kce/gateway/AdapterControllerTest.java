package com.cuso.kce.gateway;

import com.cuso.kce.gateway.api.AdapterController;
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
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(AdapterController.class)
@Import({
    ApiKeyFilter.class,
    AdapterControllerTest.TestConfig.class
})
@TestPropertySource(properties = {
    "kce.auth.api-key=test-gateway-key"
})
class AdapterControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private EngineClient engineClient;

    @Test
    void syncZhiguangPostIndexesPostAsContextResource() throws Exception {
        when(engineClient.syncZhiguangPost(
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
        )).thenReturn(Map.of(
            "status", "ok",
            "provider", "zhiguang",
            "resourceId", "zhiguang-post-262804640385601536",
            "nodeCount", 3
        ));

        mockMvc.perform(
                post("/api/v1/adapters/zhiguang/sync")
                    .header("X-API-Key", "test-gateway-key")
                    .contentType(APPLICATION_JSON)
                    .content("""
                        {
                          "postId": "262804640385601536",
                          "title": "Redis cache-aside reply notes",
                          "description": "A Zhiguang note about explaining cache-aside.",
                          "tags": ["Redis", "Java"],
                          "contentMarkdown": "Cache-aside keeps the database authoritative.",
                          "contentUrl": "https://zhiguang.example/posts/262804640385601536.md",
                          "contentSha256": "sha-demo",
                          "authorId": "42",
                          "status": "published",
                          "visible": "public"
                        }
                        """)
            )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("ok"))
            .andExpect(jsonPath("$.provider").value("zhiguang"))
            .andExpect(jsonPath("$.resourceId").value("zhiguang-post-262804640385601536"))
            .andExpect(jsonPath("$.nodeCount").value(3));

        verify(engineClient).syncZhiguangPost(
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
    }

    @TestConfiguration
    static class TestConfig {
        @Bean
        ApiKeyFilter apiKeyFilter() {
            return new ApiKeyFilter("test-gateway-key");
        }
    }
}
