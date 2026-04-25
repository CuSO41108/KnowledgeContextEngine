package com.cuso.kce.gateway;

import com.cuso.kce.gateway.api.ResourceController;
import com.cuso.kce.gateway.api.ResourceImportPathGuard;
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

import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ResourceController.class)
@Import({
    ApiKeyFilter.class,
    ResourceImportPathGuard.class,
    ResourceControllerTest.TestConfig.class
})
@TestPropertySource(properties = {
    "kce.auth.api-key=test-gateway-key",
    "kce.import.base-dir=data"
})
class ResourceControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private EngineClient engineClient;

    @Test
    void importResourcesAcceptsJsonBodyAndReturnsSuccessPayload() throws Exception {
        when(engineClient.importResources("demo_local", "data/demo-resources"))
            .thenReturn(Map.of(
                "status", "ok",
                "provider", "demo_local",
                "importedCount", 2,
                "resourceIds", List.of("redis-cache", "memcached-cache")
            ));

        mockMvc.perform(
                post("/api/v1/resources/import")
                    .header("X-API-Key", "test-gateway-key")
                    .contentType(APPLICATION_JSON)
                    .content("""
                        {
                          "provider": "demo_local",
                          "resourceDir": "data/demo-resources"
                        }
                        """)
            )
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("ok"))
            .andExpect(jsonPath("$.provider").value("demo_local"))
            .andExpect(jsonPath("$.importedCount").value(2))
            .andExpect(jsonPath("$.resourceIds[0]").value("redis-cache"));

        verify(engineClient).importResources("demo_local", "data/demo-resources");
    }

    @Test
    void importResourcesRejectsPathsOutsideConfiguredImportRoot() throws Exception {
        mockMvc.perform(
                post("/api/v1/resources/import")
                    .header("X-API-Key", "test-gateway-key")
                    .contentType(APPLICATION_JSON)
                    .content("""
                        {
                          "provider": "demo_local",
                          "resourceDir": "../outside"
                        }
                        """)
            )
            .andExpect(status().isBadRequest());

        verifyNoInteractions(engineClient);
    }

    @TestConfiguration
    static class TestConfig {
        @Bean
        ApiKeyFilter apiKeyFilter() {
            return new ApiKeyFilter("test-gateway-key");
        }
    }
}
