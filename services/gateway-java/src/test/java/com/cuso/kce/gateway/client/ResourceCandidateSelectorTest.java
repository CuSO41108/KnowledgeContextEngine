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

    @Test
    void staysStableWhenManyResourcesShareGenericReliabilityLanguage() {
        String selected = selector.selectResource(
            "写一条关于系统可靠性的 Zhiguang 回复",
            "我只想解释重复消费和死信队列，不展开削峰填谷。",
            List.of(
                new ResourceCandidateSelector.ResourceCandidate(
                    "a-zhiguang-system-reliability-overview",
                    List.of(
                        "Zhiguang System Reliability Overview",
                        "系统可靠性 / System Reliability",
                        "resource://a-zhiguang-system-reliability-overview/l2/s001/000",
                        "System reliability focuses on keeping workflows resilient under load."
                    )
                ),
                new ResourceCandidateSelector.ResourceCandidate(
                    "b-zhiguang-message-queue-delivery-guide",
                    List.of(
                        "Zhiguang Message Queue Delivery Guide",
                        "消息队列 / Message Queue",
                        "至少一次投递与幂等 / At-least-once Delivery and Idempotency",
                        "resource://b-zhiguang-message-queue-delivery-guide/l2/s002/000",
                        "Dead-letter queues help isolate poison messages, and duplicate deliveries require idempotent handlers."
                    )
                ),
                new ResourceCandidateSelector.ResourceCandidate(
                    "c-zhiguang-search-indexing-guide",
                    List.of(
                        "Zhiguang Search Indexing Guide",
                        "搜索索引 / Search Indexing",
                        "排序与刷新 / Ranking and Refresh",
                        "resource://c-zhiguang-search-indexing-guide/l2/s002/000",
                        "Incremental refresh keeps edited content searchable."
                    )
                ),
                new ResourceCandidateSelector.ResourceCandidate(
                    "d-zhiguang-distributed-tracing-guide",
                    List.of(
                        "Zhiguang Distributed Tracing Guide",
                        "分布式追踪 / Distributed Tracing",
                        "采样与日志关联 / Sampling and Log Correlation",
                        "resource://d-zhiguang-distributed-tracing-guide/l2/s002/000",
                        "Log correlation connects traces to related logs."
                    )
                )
            )
        );

        assertThat(selected).isEqualTo("b-zhiguang-message-queue-delivery-guide");
    }
}
