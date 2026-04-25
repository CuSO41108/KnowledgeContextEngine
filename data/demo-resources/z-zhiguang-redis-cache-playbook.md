# Zhiguang Redis Cache Playbook

## Redis
Redis cache-aside is a practical pattern for read-heavy flows where most reads should hit cache first.

### Cache Aside
Read path: check Redis first, fall back to the database on a miss, then write the fresh value back into Redis.

Write path: update the database first, then delete or invalidate the old Redis key so the next read repopulates the cache.

Good caveat for Zhiguang: mention the short stale window and explain that hot keys benefit most.
