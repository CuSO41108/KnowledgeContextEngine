# Zhiguang Distributed Tracing Guide

## 分布式追踪 / Distributed Tracing
Distributed tracing uses trace and span IDs to connect one user request across gateways, services, and storage calls. 在中文语境里，可以把它理解为把一次请求的上下游调用链串起来，方便定位延迟和错误。

## 采样与日志关联 / Sampling and Log Correlation
Sampling keeps telemetry cost under control, and log correlation lets engineers jump from a trace to the related logs when debugging latency spikes, partial failures, and timeout chains.
