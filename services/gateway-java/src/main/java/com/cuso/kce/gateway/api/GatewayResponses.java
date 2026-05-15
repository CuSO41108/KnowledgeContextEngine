package com.cuso.kce.gateway.api;

import java.util.List;
import java.util.Map;

final class GatewayResponses {

    private GatewayResponses() {
    }

    record ResourceImportResponse(
        String status,
        String provider,
        int importedCount,
        List<String> resourceIds
    ) {
    }

    record ZhiguangSyncResponse(
        String status,
        String provider,
        String resourceId,
        String sourceUri,
        int nodeCount
    ) {
    }

    record SessionStateResponse(
        String sessionId,
        String goal,
        String summary,
        boolean created,
        int turnCount
    ) {
    }

    record SessionCommitResponse(
        String status,
        String sessionId,
        String summary,
        int committedMemoryCount
    ) {
    }

    record QueryResponse(
        String answer,
        String traceId,
        UsedContextsResponse usedContexts,
        CompressionSummaryResponse compressionSummary
    ) {
    }

    record UsedContextsResponse(
        String sessionSummary,
        List<QueryMemoryResponse> memories,
        List<QueryResourceResponse> resources
    ) {
    }

    record QueryMemoryResponse(
        String channel,
        String type,
        String content
    ) {
    }

    record QueryResourceResponse(
        String nodeId,
        String traceNodeId,
        String nodePath,
        List<String> drilldownTrail,
        double retrievalScore,
        List<String> matchedTerms,
        String selectionReason,
        String resourceScope,
        Map<String, Double> scoreBreakdown
    ) {
    }

    record CompressionSummaryResponse(
        int beforeContextChars,
        int afterContextChars
    ) {
    }

    record ResourceTreeResponse(
        String resourceId,
        List<ResourceTreeNodeResponse> nodes
    ) {
    }

    record ResourceTreeNodeResponse(
        String nodeId,
        String nodePath,
        String level,
        String title,
        String parentNodeId
    ) {
    }

    record TraceNodeSnapshotResponse(
        String nodeId,
        String nodePath,
        String level,
        List<TraceAncestryItemResponse> ancestry,
        String snapshotContent
    ) {
    }

    record TraceAncestryItemResponse(
        String node_id,
        String node_path,
        String level
    ) {
    }

    record TraceResponse(
        String traceId,
        String question,
        String answer,
        UsedContextsResponse usedContexts,
        CompressionSummaryResponse compressionSummary,
        List<TraceNodeSnapshotResponse> nodeSnapshots
    ) {
    }

    static ResourceImportResponse resourceImport(Map<String, Object> payload) {
        return new ResourceImportResponse(
            string(payload.get("status")),
            string(payload.get("provider")),
            intValue(payload.get("importedCount")),
            stringList(payload.get("resourceIds"))
        );
    }

    static ZhiguangSyncResponse zhiguangSync(Map<String, Object> payload) {
        return new ZhiguangSyncResponse(
            string(payload.get("status")),
            string(payload.get("provider")),
            string(payload.get("resourceId")),
            string(payload.get("sourceUri")),
            intValue(payload.get("nodeCount"))
        );
    }

    static SessionStateResponse sessionState(Map<String, Object> payload) {
        return new SessionStateResponse(
            string(payload.get("sessionId")),
            string(payload.get("goal")),
            string(payload.get("summary")),
            booleanValue(payload.get("created")),
            intValue(payload.get("turnCount"))
        );
    }

    static SessionCommitResponse sessionCommit(Map<String, Object> payload) {
        return new SessionCommitResponse(
            string(payload.get("status")),
            string(payload.get("sessionId")),
            string(payload.get("summary")),
            intValue(payload.get("committedMemoryCount"))
        );
    }

    static QueryResponse query(Map<String, Object> payload) {
        return new QueryResponse(
            string(payload.get("answer")),
            string(payload.get("traceId")),
            usedContexts(payload.get("usedContexts")),
            compressionSummary(payload.get("compressionSummary"))
        );
    }

    static ResourceTreeResponse resourceTree(Map<String, Object> payload) {
        return new ResourceTreeResponse(
            string(payload.get("resourceId")),
            mapList(payload.get("nodes")).stream()
                .map(GatewayResponses::resourceTreeNode)
                .toList()
        );
    }

    static TraceNodeSnapshotResponse traceNodeSnapshot(Map<String, Object> payload) {
        return new TraceNodeSnapshotResponse(
            string(payload.get("nodeId")),
            string(payload.get("nodePath")),
            string(payload.get("level")),
            mapList(payload.get("ancestry")).stream()
                .map(GatewayResponses::traceAncestryItem)
                .toList(),
            string(payload.get("snapshotContent"))
        );
    }

    static TraceResponse trace(Map<String, Object> payload) {
        return new TraceResponse(
            string(payload.get("traceId")),
            string(payload.get("question")),
            string(payload.get("answer")),
            usedContexts(payload.get("usedContexts")),
            compressionSummary(payload.get("compressionSummary")),
            mapList(payload.get("nodeSnapshots")).stream()
                .map(GatewayResponses::traceNodeSnapshot)
                .toList()
        );
    }

    private static UsedContextsResponse usedContexts(Object value) {
        Map<String, Object> payload = map(value);
        return new UsedContextsResponse(
            string(payload.get("sessionSummary")),
            mapList(payload.get("memories")).stream()
                .map(GatewayResponses::queryMemory)
                .toList(),
            mapList(payload.get("resources")).stream()
                .map(GatewayResponses::queryResource)
                .toList()
        );
    }

    private static QueryMemoryResponse queryMemory(Map<String, Object> payload) {
        return new QueryMemoryResponse(
            string(payload.get("channel")),
            string(payload.get("type")),
            string(payload.get("content"))
        );
    }

    private static QueryResourceResponse queryResource(Map<String, Object> payload) {
        return new QueryResourceResponse(
            string(payload.get("nodeId")),
            string(payload.get("traceNodeId")),
            string(payload.get("nodePath")),
            stringList(payload.get("drilldownTrail")),
            doubleValue(payload.get("retrievalScore")),
            stringList(payload.get("matchedTerms")),
            string(payload.get("selectionReason")),
            string(payload.get("resourceScope")),
            doubleMap(payload.get("scoreBreakdown"))
        );
    }

    private static CompressionSummaryResponse compressionSummary(Object value) {
        Map<String, Object> payload = map(value);
        return new CompressionSummaryResponse(
            intValue(payload.get("beforeContextChars")),
            intValue(payload.get("afterContextChars"))
        );
    }

    private static ResourceTreeNodeResponse resourceTreeNode(Map<String, Object> payload) {
        return new ResourceTreeNodeResponse(
            string(payload.get("nodeId")),
            string(payload.get("nodePath")),
            string(payload.get("level")),
            string(payload.get("title")),
            nullableString(payload.get("parentNodeId"))
        );
    }

    private static TraceAncestryItemResponse traceAncestryItem(Map<String, Object> payload) {
        return new TraceAncestryItemResponse(
            string(payload.get("node_id")),
            string(payload.get("node_path")),
            string(payload.get("level"))
        );
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> map(Object value) {
        if (value instanceof Map<?, ?> raw) {
            return (Map<String, Object>) raw;
        }
        return Map.of();
    }

    private static List<Map<String, Object>> mapList(Object value) {
        if (!(value instanceof List<?> raw)) {
            return List.of();
        }
        return raw.stream()
            .filter(Map.class::isInstance)
            .map(GatewayResponses::map)
            .toList();
    }

    private static List<String> stringList(Object value) {
        if (!(value instanceof List<?> raw)) {
            return List.of();
        }
        return raw.stream()
            .map(GatewayResponses::string)
            .toList();
    }

    private static Map<String, Double> doubleMap(Object value) {
        return map(value).entrySet().stream()
            .collect(
                java.util.stream.Collectors.toMap(
                    Map.Entry::getKey,
                    entry -> doubleValue(entry.getValue())
                )
            );
    }

    private static String string(Object value) {
        return value == null ? "" : String.valueOf(value);
    }

    private static String nullableString(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    private static int intValue(Object value) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        try {
            return Integer.parseInt(string(value));
        } catch (NumberFormatException ex) {
            return 0;
        }
    }

    private static double doubleValue(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        try {
            return Double.parseDouble(string(value));
        } catch (NumberFormatException ex) {
            return 0.0;
        }
    }

    private static boolean booleanValue(Object value) {
        if (value instanceof Boolean bool) {
            return bool;
        }
        return Boolean.parseBoolean(string(value));
    }
}
