package com.cuso.kce.gateway.api;

import com.cuso.kce.gateway.client.EngineClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/resources")
public class ResourceController {

    private final EngineClient engineClient;

    public ResourceController(EngineClient engineClient) {
        this.engineClient = engineClient;
    }

    @PostMapping("/import")
    public Map<String, Object> importResources(@RequestBody ResourceImportRequest request) throws IOException {
        return engineClient.importResources(request.provider(), request.resourceDir());
    }

    public record ResourceImportRequest(String provider, String resourceDir) {
    }
}
