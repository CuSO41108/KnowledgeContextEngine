package com.cuso.kce.gateway.api;

import com.cuso.kce.gateway.client.EngineClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;

@RestController
@RequestMapping("/api/v1/resources")
public class ResourceController {

    private final EngineClient engineClient;
    private final ResourceImportPathGuard resourceImportPathGuard;

    public ResourceController(
        EngineClient engineClient,
        ResourceImportPathGuard resourceImportPathGuard
    ) {
        this.engineClient = engineClient;
        this.resourceImportPathGuard = resourceImportPathGuard;
    }

    @PostMapping("/import")
    public GatewayResponses.ResourceImportResponse importResources(@RequestBody ResourceImportRequest request) throws IOException {
        resourceImportPathGuard.validate(request.resourceDir());
        return GatewayResponses.resourceImport(engineClient.importResources(request.provider(), request.resourceDir()));
    }

    @GetMapping("/nodes/{nodeId}")
    public GatewayResponses.TraceNodeSnapshotResponse getResourceNode(@PathVariable String nodeId) {
        return GatewayResponses.traceNodeSnapshot(engineClient.getResourceNode(nodeId));
    }

    @GetMapping("/{resourceId}/tree")
    public GatewayResponses.ResourceTreeResponse getResourceTree(@PathVariable String resourceId) {
        return GatewayResponses.resourceTree(engineClient.getResourceTree(resourceId));
    }

    public record ResourceImportRequest(String provider, String resourceDir) {
    }
}
