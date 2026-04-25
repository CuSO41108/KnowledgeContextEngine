package com.cuso.kce.gateway.client;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class EngineClient {

    private final RestClient restClient;
    private final Map<String, String> providerDefaultResourceIds = new ConcurrentHashMap<>();

    public EngineClient(@Value("${kce.engine.base-url}") String engineBaseUrl) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(10_000);
        requestFactory.setReadTimeout(30_000);
        this.restClient = RestClient.builder()
            .requestFactory(requestFactory)
            .baseUrl(engineBaseUrl)
            .build();
    }

    public Map<String, Object> importResources(String provider, String resourceDir) throws IOException {
        List<Path> markdownFiles = Files.walk(Path.of(resourceDir))
            .filter(Files::isRegularFile)
            .filter(path -> path.getFileName().toString().toLowerCase(Locale.ROOT).endsWith(".md"))
            .sorted(Comparator.naturalOrder())
            .toList();

        List<String> resourceIds = new ArrayList<>();
        for (Path markdownFile : markdownFiles) {
            String resourceId = slugify(stripExtension(markdownFile.getFileName().toString()));
            String markdown = Files.readString(markdownFile);
            restClient.post()
                .uri("/internal/resources/index")
                .contentType(MediaType.APPLICATION_JSON)
                .body(Map.of(
                    "resource_slug", resourceId,
                    "markdown", markdown
                ))
                .retrieve()
                .toEntity(Map.class);
            resourceIds.add(resourceId);
        }

        if (!resourceIds.isEmpty()) {
            providerDefaultResourceIds.put(provider, resourceIds.get(resourceIds.size() - 1));
        }

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("status", "ok");
        response.put("provider", provider);
        response.put("importedCount", resourceIds.size());
        response.put("resourceIds", resourceIds);
        return response;
    }

    public Map<String, Object> query(
        String sessionId,
        String internalUserId,
        String provider,
        String message,
        String goal
    ) {
        String resourceId = providerDefaultResourceIds.get(provider);
        if (resourceId == null) {
            throw new IllegalStateException("No default resource imported for provider: " + provider);
        }

        List<Map<String, String>> turns = List.of(Map.of("role", "user", "content", message));
        Map<String, Object> summaryResponse = post("/internal/session/summarize", Map.of(
            "session_goal", goal,
            "turns", turns
        ));
        String sessionSummary = String.valueOf(summaryResponse.get("summary"));

        List<String> selectedResourcePaths = resolveSelectedResourcePaths(resourceId);
        Map<String, Object> memoryResponse = post("/internal/memory/extract", Map.of(
            "session_goal", goal,
            "turns", turns,
            "selected_resource_paths", selectedResourcePaths
        ));
        List<String> memoryItems = extractMemoryContents(memoryResponse);

        return post("/internal/context/query", Map.of(
            "question", message,
            "resource_id", resourceId,
            "session_summary", sessionSummary,
            "memory_items", memoryItems
        ));
    }

    public Map<String, Object> getTrace(String traceId) {
        return restClient.get()
            .uri("/internal/traces/{traceId}", traceId)
            .retrieve()
            .body(Map.class);
    }

    @SuppressWarnings("unchecked")
    private List<String> resolveSelectedResourcePaths(String resourceId) {
        Map<String, Object> treeResponse = restClient.get()
            .uri("/internal/resources/{resourceId}/tree", resourceId)
            .retrieve()
            .body(Map.class);

        List<Map<String, Object>> nodes = (List<Map<String, Object>>) treeResponse.getOrDefault("nodes", List.of());
        List<String> l2Paths = nodes.stream()
            .filter(node -> "l2".equals(node.get("level")))
            .map(node -> String.valueOf(node.get("nodePath")))
            .toList();
        if (!l2Paths.isEmpty()) {
            return List.of(l2Paths.get(0));
        }
        return nodes.stream()
            .filter(node -> "l1".equals(node.get("level")))
            .map(node -> String.valueOf(node.get("nodePath")))
            .findFirst()
            .map(List::of)
            .orElse(List.of());
    }

    @SuppressWarnings("unchecked")
    private List<String> extractMemoryContents(Map<String, Object> memoryResponse) {
        List<Map<String, Object>> candidates = (List<Map<String, Object>>) memoryResponse.getOrDefault("candidates", List.of());
        return candidates.stream()
            .map(candidate -> String.valueOf(candidate.get("content")))
            .toList();
    }

    private Map<String, Object> post(String uri, Map<String, Object> body) {
        return restClient.post()
            .uri(uri)
            .contentType(MediaType.APPLICATION_JSON)
            .body(body)
            .retrieve()
            .body(Map.class);
    }

    private String stripExtension(String fileName) {
        int dotIndex = fileName.lastIndexOf('.');
        return dotIndex >= 0 ? fileName.substring(0, dotIndex) : fileName;
    }

    private String slugify(String value) {
        return value.toLowerCase(Locale.ROOT)
            .replaceAll("[^a-z0-9]+", "-")
            .replaceAll("^-+|-+$", "");
    }
}
