package com.cuso.kce.gateway.api;

import com.cuso.kce.gateway.client.EngineClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/traces")
public class TraceController {

    private final EngineClient engineClient;

    public TraceController(EngineClient engineClient) {
        this.engineClient = engineClient;
    }

    @GetMapping("/{traceId}")
    public Map<String, Object> getTrace(@PathVariable String traceId) {
        return engineClient.getTrace(traceId);
    }
}
