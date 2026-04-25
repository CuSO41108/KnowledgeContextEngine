package com.cuso.kce.gateway.identity;

import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.util.UUID;

@Service
public class IdentityService {

    public String resolveInternalUserId(String provider, String externalUserId) {
        String key = provider + ":" + externalUserId;
        return UUID.nameUUIDFromBytes(key.getBytes(StandardCharsets.UTF_8)).toString();
    }
}
