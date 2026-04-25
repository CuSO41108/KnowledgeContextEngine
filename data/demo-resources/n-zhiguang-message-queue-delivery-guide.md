# Zhiguang Message Queue Delivery Guide

## 消息队列 / Message Queue
A message queue decouples producers and consumers so burst traffic can be buffered instead of failing synchronous calls. 在中文语境里，消息队列常用来削峰填谷、异步化和解耦。

## 至少一次投递与幂等 / At-least-once Delivery and Idempotency
At-least-once delivery means consumers may receive duplicate messages, so handlers should be idempotent and retry-safe. Dead-letter queues help isolate poison messages instead of blocking the whole pipeline.
