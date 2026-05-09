package com.cuso.kce.gateway.api;

import com.cuso.kce.gateway.client.EngineClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/adapters")
public class AdapterController {

    private final EngineClient engineClient;

    public AdapterController(EngineClient engineClient) {
        this.engineClient = engineClient;
    }

    @PostMapping("/zhiguang/sync")
    public Map<String, Object> syncZhiguangPost(@RequestBody ZhiguangSyncRequest request) {
        return engineClient.syncZhiguangPost(
            request.postId(),
            request.title(),
            request.description(),
            request.tags(),
            request.contentMarkdown(),
            request.contentUrl(),
            request.contentSha256(),
            request.authorId(),
            request.status(),
            request.visible()
        );
    }

    public record ZhiguangSyncRequest(
        String postId,
        String title,
        String description,
        List<String> tags,
        String contentMarkdown,
        String contentUrl,
        String contentSha256,
        String authorId,
        String status,
        String visible
    ) {
    }
}
