package com.cuso.kce.gateway;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = "kce.auth.api-key=test-gateway-key")
class ApiKeyFilterTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void missingApiKeyReturnsUnauthorized() throws Exception {
        mockMvc.perform(get("/api/v1/health"))
            .andExpect(status().isUnauthorized())
            .andExpect(content().string(""));
    }

    @Test
    void validApiKeyAllowsHealthCheck() throws Exception {
        mockMvc.perform(get("/api/v1/health").header("X-API-Key", "test-gateway-key"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("ok"))
            .andExpect(jsonPath("$.service").value("gateway-java"));
    }

    @Test
    void nestedApiPathAlsoRequiresApiKey() throws Exception {
        mockMvc.perform(get("/api/v1/sessions/demo/query"))
            .andExpect(status().isUnauthorized())
            .andExpect(content().string(""));
    }
}
