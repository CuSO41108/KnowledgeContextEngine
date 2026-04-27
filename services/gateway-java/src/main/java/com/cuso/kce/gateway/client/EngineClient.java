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
import java.util.LinkedHashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Stream;

@Service
public class EngineClient {

    private final RestClient restClient;
    private final Map<String, ResourceTreeMetadata> resourceTreeMetadataById = new ConcurrentHashMap<>();
    private final ResourceCandidateSelector resourceCandidateSelector = new ResourceCandidateSelector();

    private record ResourceTreeMetadata(List<String> evidenceTexts) {
    }

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
        List<Path> markdownFiles;
        try (Stream<Path> paths = Files.walk(Path.of(resourceDir))) {
            markdownFiles = paths
                .filter(Files::isRegularFile)
                .filter(path -> path.getFileName().toString().toLowerCase(Locale.ROOT).endsWith(".md"))
                .sorted(Comparator.naturalOrder())
                .toList();
        }

        List<String> resourceIds = new ArrayList<>();
        for (Path markdownFile : markdownFiles) {
            String resourceId = slugify(stripExtension(markdownFile.getFileName().toString()));
            String markdown = Files.readString(markdownFile);
            Map<String, Object> indexResponse = restClient.post()
                .uri("/internal/resources/index")
                .contentType(MediaType.APPLICATION_JSON)
                .body(Map.of(
                    "provider", provider,
                    "resource_slug", resourceId,
                    "markdown", markdown,
                    "source_uri", markdownFile.toAbsolutePath().toString()
                ))
                .retrieve()
                .body(Map.class);
            resourceTreeMetadataById.put(resourceId, buildResourceTreeMetadata(resourceId, indexResponse));
            resourceIds.add(resourceId);
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
        String externalUserId,
        String message,
        String goal
    ) {
        Map<String, Object> sessionState = createSession(sessionId, internalUserId, provider, externalUserId, goal);
        List<String> resourceIds = refreshProviderResourceMetadata(provider);
        if (resourceIds.isEmpty()) {
            throw new IllegalStateException("No resources imported for provider: " + provider);
        }
        String resourceId = selectResourceId(resourceIds, message, goal);

        List<Map<String, String>> turns = List.of(Map.of("role", "user", "content", message));
        Map<String, Object> summaryResponse = post("/internal/session/summarize", Map.of(
            "session_goal", goal,
            "turns", turns
        ));
        String sessionSummary = mergeSessionSummaries(
            String.valueOf(sessionState.getOrDefault("summary", "")),
            String.valueOf(summaryResponse.getOrDefault("summary", ""))
        );

        Map<String, Object> memoryResponse = post("/internal/memory/extract", Map.of(
            "session_goal", goal,
            "turns", turns
        ));
        List<String> memoryItems = mergeMemoryContents(
            extractRecalledMemoryContents(getUserMemories(internalUserId)),
            extractCandidateMemoryContents(memoryResponse)
        );

        return post("/internal/context/query", Map.of(
            "question", message,
            "resource_id", resourceId,
            "session_summary", sessionSummary,
            "memory_items", memoryItems,
            "session_key", sessionId,
            "user_id", internalUserId
        ));
    }

    public Map<String, Object> createSession(
        String sessionId,
        String internalUserId,
        String provider,
        String externalUserId,
        String goal
    ) {
        return post("/internal/sessions", Map.of(
            "session_key", sessionId,
            "user_id", internalUserId,
            "provider", provider,
            "external_user_id", externalUserId,
            "goal", normalizeOptional(goal)
        ));
    }

    public Map<String, Object> commitSession(
        String sessionId,
        String internalUserId,
        String userMessage,
        String assistantAnswer,
        String traceId,
        String goal
    ) {
        return post(
            "/internal/sessions/" + sessionId + "/commit",
            Map.of(
                "user_id", internalUserId,
                "goal", normalizeOptional(goal),
                "user_message", userMessage,
                "assistant_answer", assistantAnswer,
                "trace_id", traceId
            )
        );
    }

    public Map<String, Object> getTrace(String traceId) {
        return restClient.get()
            .uri("/internal/traces/{traceId}", traceId)
            .retrieve()
            .body(Map.class);
    }

    public Map<String, Object> getTraceNodeSnapshot(String traceId, String nodeId) {
        return restClient.get()
            .uri("/internal/traces/{traceId}/nodes/{nodeId}", traceId, nodeId)
            .retrieve()
            .body(Map.class);
    }

    public Map<String, Object> getResourceNode(String nodeId) {
        return restClient.get()
            .uri("/internal/resources/nodes/{nodeId}", nodeId)
            .retrieve()
            .body(Map.class);
    }

    public Map<String, Object> getResourceTree(String resourceId) {
        return restClient.get()
            .uri("/internal/resources/{resourceId}/tree", resourceId)
            .retrieve()
            .body(Map.class);
    }

    private String selectResourceId(List<String> resourceIds, String message, String goal) {
        if (resourceIds.size() == 1) {
            return resourceIds.getFirst();
        }

        List<ResourceCandidateSelector.ResourceCandidate> candidates = resourceIds.stream()
            .map(resourceId -> {
                ResourceTreeMetadata metadata = getResourceTreeMetadata(resourceId);
                return new ResourceCandidateSelector.ResourceCandidate(
                    resourceId,
                    metadata.evidenceTexts()
                );
            })
            .toList();

        return resourceCandidateSelector.selectResource(goal, message, candidates);
    }

    private ResourceTreeMetadata getResourceTreeMetadata(String resourceId) {
        return resourceTreeMetadataById.computeIfAbsent(resourceId, this::fetchResourceTreeMetadata);
    }

    @SuppressWarnings("unchecked")
    private List<String> refreshProviderResourceMetadata(String provider) {
        Map<String, Object> providerTreesResponse = restClient.get()
            .uri("/internal/resources/providers/{provider}/trees", provider)
            .retrieve()
            .body(Map.class);

        List<Map<String, Object>> resourceTrees =
            (List<Map<String, Object>>) providerTreesResponse.getOrDefault("resources", List.of());
        List<String> resourceIds = new ArrayList<>();
        for (Map<String, Object> resourceTree : resourceTrees) {
            String resourceId = String.valueOf(resourceTree.get("resourceId"));
            resourceTreeMetadataById.put(resourceId, buildResourceTreeMetadata(resourceId, resourceTree));
            resourceIds.add(resourceId);
        }
        return List.copyOf(resourceIds);
    }

    @SuppressWarnings("unchecked")
    private ResourceTreeMetadata fetchResourceTreeMetadata(String resourceId) {
        Map<String, Object> treeResponse = restClient.get()
            .uri("/internal/resources/{resourceId}/tree", resourceId)
            .retrieve()
            .body(Map.class);

        return buildResourceTreeMetadata(resourceId, treeResponse);
    }

    @SuppressWarnings("unchecked")
    private ResourceTreeMetadata buildResourceTreeMetadata(String resourceId, Map<String, Object> treeResponse) {
        List<Map<String, Object>> nodes = (List<Map<String, Object>>) treeResponse.getOrDefault("nodes", List.of());
        List<String> evidenceTexts = new ArrayList<>();
        evidenceTexts.add(resourceId);
        for (Map<String, Object> node : nodes) {
            evidenceTexts.add(readNodeField(node, "title"));
            evidenceTexts.add(readNodeField(node, "content"));

            String nodePath = readNodeField(node, "nodePath", "node_path");
            evidenceTexts.add(nodePath);
        }

        return new ResourceTreeMetadata(List.copyOf(evidenceTexts));
    }

    private String readNodeField(Map<String, Object> node, String... keys) {
        for (String key : keys) {
            Object value = node.get(key);
            if (value != null) {
                return String.valueOf(value);
            }
        }
        return "";
    }

    @SuppressWarnings("unchecked")
    private List<String> extractCandidateMemoryContents(Map<String, Object> memoryResponse) {
        List<Map<String, Object>> candidates = (List<Map<String, Object>>) memoryResponse.getOrDefault("candidates", List.of());
        return candidates.stream()
            .map(candidate -> String.valueOf(candidate.get("content")))
            .toList();
    }

    @SuppressWarnings("unchecked")
    private List<String> extractRecalledMemoryContents(Map<String, Object> memoryResponse) {
        List<Map<String, Object>> memories = (List<Map<String, Object>>) memoryResponse.getOrDefault("memories", List.of());
        return memories.stream()
            .map(memory -> String.valueOf(memory.get("content")))
            .toList();
    }

    private Map<String, Object> getUserMemories(String internalUserId) {
        return restClient.get()
            .uri("/internal/users/{userId}/memories", internalUserId)
            .retrieve()
            .body(Map.class);
    }

    private List<String> mergeMemoryContents(List<String> recalledMemoryItems, List<String> currentMemoryItems) {
        LinkedHashSet<String> merged = new LinkedHashSet<>();
        merged.addAll(recalledMemoryItems);
        merged.addAll(currentMemoryItems);
        return List.copyOf(merged);
    }

    private String mergeSessionSummaries(String existingSummary, String currentSummary) {
        String normalizedExisting = normalizeOptional(existingSummary);
        String normalizedCurrent = normalizeOptional(currentSummary);
        if (normalizedExisting.isBlank()) {
            return normalizedCurrent;
        }
        if (normalizedCurrent.isBlank()) {
            return normalizedExisting;
        }
        if (normalizedExisting.equals(normalizedCurrent)) {
            return normalizedExisting;
        }
        return normalizedExisting + " Historical context: " + normalizedCurrent;
    }

    private Map<String, Object> post(String uri, Map<String, Object> body) {
        return restClient.post()
            .uri(uri)
            .contentType(MediaType.APPLICATION_JSON)
            .body(body)
            .retrieve()
            .body(Map.class);
    }

    private String normalizeOptional(String value) {
        return value == null ? "" : value;
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
