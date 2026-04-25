package com.cuso.kce.gateway.api;

import com.cuso.kce.gateway.client.EngineClient;
import com.cuso.kce.gateway.identity.IdentityService;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/sessions")
public class SessionController {

    private final IdentityService identityService;
    private final EngineClient engineClient;

    public SessionController(IdentityService identityService, EngineClient engineClient) {
        this.identityService = identityService;
        this.engineClient = engineClient;
    }

    @PostMapping("/{sessionId}/query")
    public Map<String, Object> query(@PathVariable String sessionId, @RequestBody SessionQueryRequest request) {
        String internalUserId = identityService.resolveInternalUserId(request.provider(), request.externalUserId());
        return engineClient.query(
            sessionId,
            internalUserId,
            request.provider(),
            request.message(),
            request.goal()
        );
    }

    public record SessionQueryRequest(
        String provider,
        String externalUserId,
        String message,
        String goal
    ) {
    }
}
