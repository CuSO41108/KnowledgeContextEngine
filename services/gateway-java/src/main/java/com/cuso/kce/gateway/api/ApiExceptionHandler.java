package com.cuso.kce.gateway.api;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.server.ResponseStatusException;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ErrorResponse> handleResponseStatus(ResponseStatusException ex) {
        HttpStatus status = HttpStatus.valueOf(ex.getStatusCode().value());
        return ResponseEntity.status(status).body(new ErrorResponse(
            codeFor(status),
            ex.getReason() == null ? status.getReasonPhrase() : ex.getReason(),
            null
        ));
    }

    @ExceptionHandler(RestClientResponseException.class)
    public ResponseEntity<ErrorResponse> handleUpstreamHttp(RestClientResponseException ex) {
        HttpStatus status = HttpStatus.resolve(ex.getStatusCode().value());
        HttpStatus responseStatus = status != null && status.is4xxClientError() ? status : HttpStatus.BAD_GATEWAY;
        return ResponseEntity.status(responseStatus).body(new ErrorResponse(
            "UPSTREAM_ERROR",
            upstreamMessage(ex),
            ex.getStatusCode().value()
        ));
    }

    @ExceptionHandler(ResourceAccessException.class)
    public ResponseEntity<ErrorResponse> handleUpstreamAccess(ResourceAccessException ex) {
        return ResponseEntity.status(HttpStatus.GATEWAY_TIMEOUT).body(new ErrorResponse(
            "UPSTREAM_TIMEOUT",
            ex.getMessage() == null ? "KCE engine is unavailable or timed out" : ex.getMessage(),
            null
        ));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneric(Exception ex) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(new ErrorResponse(
            "INTERNAL_ERROR",
            ex.getMessage() == null ? "internal gateway error" : ex.getMessage(),
            null
        ));
    }

    private String upstreamMessage(RestClientResponseException ex) {
        String body = ex.getResponseBodyAsString();
        if (body != null && !body.isBlank()) {
            return body;
        }
        return ex.getStatusText() == null || ex.getStatusText().isBlank()
            ? "KCE engine request failed"
            : ex.getStatusText();
    }

    private String codeFor(HttpStatus status) {
        return status.is4xxClientError() ? "INVALID_REQUEST" : "GATEWAY_ERROR";
    }

    public record ErrorResponse(
        String code,
        String message,
        Integer upstreamStatus
    ) {
    }
}
