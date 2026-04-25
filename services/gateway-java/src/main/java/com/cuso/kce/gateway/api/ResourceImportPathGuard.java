package com.cuso.kce.gateway.api;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;

import java.nio.file.Path;

@Component
public class ResourceImportPathGuard {

    private final Path allowedImportRoot;
    private final Path workingDirectory;

    public ResourceImportPathGuard(@Value("${kce.import.base-dir:data}") String importBaseDir) {
        this.workingDirectory = Path.of("").toAbsolutePath().normalize();
        this.allowedImportRoot = resolvePath(importBaseDir);
    }

    public void validate(String resourceDir) {
        if (resourceDir == null || resourceDir.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "resourceDir is required");
        }

        Path requestedPath = resolvePath(resourceDir);
        if (!requestedPath.startsWith(allowedImportRoot)) {
            throw new ResponseStatusException(
                HttpStatus.BAD_REQUEST,
                "resourceDir must stay within the configured import root"
            );
        }
    }

    private Path resolvePath(String rawPath) {
        Path path = Path.of(rawPath.trim());
        if (!path.isAbsolute()) {
            path = workingDirectory.resolve(path);
        }
        return path.normalize();
    }
}
