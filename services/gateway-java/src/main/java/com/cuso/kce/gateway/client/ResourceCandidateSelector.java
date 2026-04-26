package com.cuso.kce.gateway.client;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

final class ResourceCandidateSelector {

    private static final Pattern LATIN_TERM_PATTERN = Pattern.compile("[a-z0-9]+(?:-[a-z0-9]+)*");
    private static final Pattern CJK_SEQUENCE_PATTERN = Pattern.compile("[\\p{IsHan}]{2,}");
    private static final Pattern EXCLUDED_SEGMENT_PATTERN = Pattern.compile("(?:不展开|不讲|不讨论|不解释)([^。；;!?！？]+)");
    private static final Pattern FOCUS_SEGMENT_PATTERN = Pattern.compile(
        "(?:只想|想要|想)(?:解释|讲|聊|覆盖)([^。；;!?！？]+?)(?:，|,|不展开|不讲|不讨论|不解释|$)"
    );
    private static final Set<String> ENGLISH_STOPWORDS = Set.of(
        "a",
        "an",
        "and",
        "about",
        "answer",
        "draft",
        "explain",
        "for",
        "how",
        "i",
        "if",
        "on",
        "please",
        "reply",
        "should",
        "the",
        "to",
        "write",
        "zhiguang"
    );
    private static final Map<String, List<String>> QUERY_TERM_ALIASES = new LinkedHashMap<>();

    static {
        QUERY_TERM_ALIASES.put("采样", List.of("sampling"));
        QUERY_TERM_ALIASES.put("日志关联", List.of("log correlation"));
        QUERY_TERM_ALIASES.put("调用链", List.of("call chain"));
        QUERY_TERM_ALIASES.put("幂等", List.of("idempotent", "idempotency"));
        QUERY_TERM_ALIASES.put("死信队列", List.of("dead-letter", "dead-letter queues"));
        QUERY_TERM_ALIASES.put("重复消费", List.of("duplicate", "duplicate messages", "duplicate deliveries"));
        QUERY_TERM_ALIASES.put("增量刷新", List.of("incremental refresh"));
        QUERY_TERM_ALIASES.put("排序信号", List.of("ranking"));
        QUERY_TERM_ALIASES.put("倒排索引", List.of("inverted index"));
    }

    record ResourceCandidate(String resourceId, List<String> evidenceTexts) {
    }

    String selectResource(
        String goal,
        String message,
        List<ResourceCandidate> candidates
    ) {
        if (candidates.isEmpty()) {
            throw new IllegalArgumentException("Expected at least one resource candidate.");
        }

        List<String> focusTerms = expandTerms(buildTerms(extractSegments(FOCUS_SEGMENT_PATTERN, message)));
        List<String> messageTerms = expandTerms(buildTerms(removeExcludedSegments(message)));
        List<String> goalTerms = expandTerms(buildTerms(goal));
        List<String> excludedTerms = expandTerms(buildTerms(extractSegments(EXCLUDED_SEGMENT_PATTERN, message)));
        if (focusTerms.isEmpty() && messageTerms.isEmpty() && goalTerms.isEmpty()) {
            return candidates.getFirst().resourceId();
        }

        ResourceCandidate bestCandidate = candidates.getFirst();
        int bestScore = Integer.MIN_VALUE;

        for (ResourceCandidate candidate : candidates) {
            int score = scoreCandidate(focusTerms, candidate, 16)
                + scoreCandidate(messageTerms, candidate, 10)
                + scoreCandidate(goalTerms, candidate, 4)
                - scoreCandidate(excludedTerms, candidate, 9);
            if (score > bestScore) {
                bestCandidate = candidate;
                bestScore = score;
            }
        }

        return bestCandidate.resourceId();
    }

    private int scoreCandidate(List<String> queryTerms, ResourceCandidate candidate, int weight) {
        String candidateText = candidate.evidenceTexts().stream()
            .filter(Objects::nonNull)
            .map(text -> text.toLowerCase(Locale.ROOT))
            .collect(Collectors.joining("\n"));

        int score = 0;
        for (String term : queryTerms) {
            if (candidateText.contains(term)) {
                score += weight + Math.min(term.length(), 10);
            }
        }

        return score;
    }

    private List<String> buildTerms(String... values) {
        LinkedHashSet<String> terms = new LinkedHashSet<>();
        for (String value : values) {
            if (value == null || value.isBlank()) {
                continue;
            }

            String normalized = value.toLowerCase(Locale.ROOT);
            Matcher latinMatcher = LATIN_TERM_PATTERN.matcher(normalized);
            while (latinMatcher.find()) {
                String term = latinMatcher.group();
                if (term.length() > 1 && !ENGLISH_STOPWORDS.contains(term)) {
                    terms.add(term);
                }
            }

            Matcher cjkMatcher = CJK_SEQUENCE_PATTERN.matcher(value);
            while (cjkMatcher.find()) {
                addChineseTerms(terms, cjkMatcher.group());
            }
        }

        return new ArrayList<>(terms);
    }

    private List<String> buildTerms(List<String> values) {
        return buildTerms(values.toArray(String[]::new));
    }

    private List<String> expandTerms(List<String> terms) {
        LinkedHashSet<String> expandedTerms = new LinkedHashSet<>(terms);
        for (String term : terms) {
            List<String> aliases = QUERY_TERM_ALIASES.get(term);
            if (aliases != null) {
                expandedTerms.addAll(aliases);
            }
        }
        return new ArrayList<>(expandedTerms);
    }

    private List<String> extractSegments(Pattern pattern, String value) {
        if (value == null || value.isBlank()) {
            return List.of();
        }

        List<String> segments = new ArrayList<>();
        Matcher matcher = pattern.matcher(value);
        while (matcher.find()) {
            segments.add(matcher.group(1));
        }
        return segments;
    }

    private String removeExcludedSegments(String value) {
        if (value == null || value.isBlank()) {
            return "";
        }
        return value
            .replace("不展开", "\n")
            .replace("不讲", "\n")
            .replace("不讨论", "\n")
            .replace("不解释", "\n");
    }

    private void addChineseTerms(Set<String> terms, String sequence) {
        if (sequence.length() <= 4) {
            terms.add(sequence);
            return;
        }

        for (int size = 4; size >= 2; size--) {
            for (int index = 0; index <= sequence.length() - size; index++) {
                terms.add(sequence.substring(index, index + size));
            }
        }
    }
}
