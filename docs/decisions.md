# Architecture decisions

1. **Offline-first validation** — prevents structural CI from depending on external hosts.
2. **JSON as integration boundary** — clients do not need to understand legacy M3U quirks.
3. **Read-only dashboard** — catalogue review is separated from playback.
4. **Original source preserved during migration** — no destructive move until regression evidence exists.
5. **Authorization is external to syntax** — a URL being present never implies permission to access or redistribute it.
