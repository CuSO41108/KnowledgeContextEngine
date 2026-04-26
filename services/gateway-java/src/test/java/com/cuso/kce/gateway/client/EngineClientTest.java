package com.cuso.kce.gateway.client;

import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;

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
}
