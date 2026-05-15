package com.cuso.kce.gateway.api;

import com.cuso.kce.gateway.client.EngineClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/traces")
public class TraceController {

    private final EngineClient engineClient;

    public TraceController(EngineClient engineClient) {
        this.engineClient = engineClient;
    }

    @GetMapping("/{traceId}")
    public GatewayResponses.TraceResponse getTrace(@PathVariable String traceId) {
        return GatewayResponses.trace(engineClient.getTrace(traceId));
    }

    @GetMapping("/{traceId}/nodes/{nodeId}")
    public GatewayResponses.TraceNodeSnapshotResponse getTraceNodeSnapshot(
        @PathVariable String traceId,
        @PathVariable String nodeId
    ) {
        return GatewayResponses.traceNodeSnapshot(engineClient.getTraceNodeSnapshot(traceId, nodeId));
    }
}
