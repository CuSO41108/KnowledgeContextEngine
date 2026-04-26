# Zhiguang Search Indexing Guide

## 搜索索引 / Search Indexing
Search indexing usually starts from an inverted index so queries can map terms to matching documents quickly. 在中文语境里，可以把它理解为先建“词 -> 文档”的倒排表，再做排序和召回。

## 排序与刷新 / Ranking and Refresh
Ranking combines term matching, recency, and quality signals, while incremental refresh keeps new or edited content searchable without rebuilding the whole index from scratch.
