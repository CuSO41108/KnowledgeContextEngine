package com.cuso.kce.gateway.client;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class ResourceCandidateSelectorTest {

    private final ResourceCandidateSelector selector = new ResourceCandidateSelector();

    @Test
    void selectsRedisPlaybookForCacheAsideQuery() {
        String selected = selector.selectResource(
            "write a Zhiguang reply about Redis cache-aside",
            "I am replying on Zhiguang. How should I explain Redis cache-aside briefly?",
            List.of(
                new ResourceCandidateSelector.ResourceCandidate(
                    "m-zhiguang-distributed-tracing-guide",
                    List.of(
                        "Zhiguang Distributed Tracing Guide",
                        "分布式追踪 / Distributed Tracing",
                        "采样与日志关联 / Sampling and Log Correlation"
                    )
                ),
                new ResourceCandidateSelector.ResourceCandidate(
                    "z-zhiguang-redis-cache-playbook",
                    List.of(
                        "Zhiguang Redis Cache Playbook",
                        "Redis",
                        "Cache Aside"
                    )
                )
            )
        );

        assertThat(selected).isEqualTo("z-zhiguang-redis-cache-playbook");
    }

    @Test
    void selectsDistributedTracingGuideForTracingQuery() {
        String selected = selector.selectResource(
            "写一条关于分布式追踪的 Zhiguang 回复",
            "我想用通俗一点但不失专业度的方式解释分布式追踪，请覆盖 trace、span、调用链、采样和日志关联。",
            List.of(
                new ResourceCandidateSelector.ResourceCandidate(
                    "n-zhiguang-message-queue-delivery-guide",
                    List.of(
                        "Zhiguang Message Queue Delivery Guide",
                        "消息队列 / Message Queue",
                        "至少一次投递与幂等 / At-least-once Delivery and Idempotency"
                    )
                ),
                new ResourceCandidateSelector.ResourceCandidate(
                    "m-zhiguang-distributed-tracing-guide",
                    List.of(
                        "Zhiguang Distributed Tracing Guide",
                        "分布式追踪 / Distributed Tracing",
                        "采样与日志关联 / Sampling and Log Correlation"
                    )
                ),
                new ResourceCandidateSelector.ResourceCandidate(
                    "z-zhiguang-redis-cache-playbook",
                    List.of(
                        "Zhiguang Redis Cache Playbook",
                        "Redis",
                        "Cache Aside"
                    )
                )
            )
        );

        assertThat(selected).isEqualTo("m-zhiguang-distributed-tracing-guide");
    }
}
