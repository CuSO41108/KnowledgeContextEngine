package com.cuso.kce.gateway.client;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

final class ResourceCandidateSelector {

    private static final Pattern LATIN_TERM_PATTERN = Pattern.compile("[a-z0-9]+(?:-[a-z0-9]+)*");
    private static final Pattern CJK_SEQUENCE_PATTERN = Pattern.compile("[\\p{IsHan}]{2,}");
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

        List<String> queryTerms = buildTerms(goal, message);
        if (queryTerms.isEmpty()) {
            return candidates.getFirst().resourceId();
        }

        ResourceCandidate bestCandidate = candidates.getFirst();
        int bestScore = Integer.MIN_VALUE;

        for (ResourceCandidate candidate : candidates) {
            int score = scoreCandidate(queryTerms, candidate);
            if (score > bestScore) {
                bestCandidate = candidate;
                bestScore = score;
            }
        }

        return bestCandidate.resourceId();
    }

    private int scoreCandidate(List<String> queryTerms, ResourceCandidate candidate) {
        String candidateText = candidate.evidenceTexts().stream()
            .filter(Objects::nonNull)
            .map(text -> text.toLowerCase(Locale.ROOT))
            .collect(Collectors.joining("\n"));

        int score = 0;
        for (String term : queryTerms) {
            if (candidateText.contains(term)) {
                score += 2 + Math.min(term.length(), 10);
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
