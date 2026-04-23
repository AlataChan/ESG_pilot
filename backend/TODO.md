# Backend TODO

## Deferred: knowledge_service.py V1 async/blocking-I/O rewrite

**Status**: Deferred from P1 cleanup round on 2026-04-24.

**Context**: `backend/app/services/knowledge_service.py` contains blocking `sqlite3`
operations such as `cursor.execute`, `conn.commit`, and `_get_connection()` inside
`async def` methods. That blocks the event loop under concurrent load.

**Why deferred**:
- `knowledge_service_v2.py` is still a subset of V1 and does not cover the full V1
  method surface.
- The V1-backed advanced knowledge routes do not have integration coverage yet.
- Current behavior works for low-concurrency local usage, so the risk of a rushed
  rewrite is higher than the current runtime cost.

**Prerequisites before tackling**:
1. Add integration tests for the V1-backed knowledge routes such as preview,
   processing, search, and supported-types flows.
2. Either port the missing methods to V2 or introduce a dedicated async SQLite path
   (for example `aiosqlite`) with explicit compatibility coverage.
3. Revisit remaining V1 callers after the P1 dead initialization cleanup removed the
   unused service wiring from RAG, extraction, and knowledge search tool paths.
