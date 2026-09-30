# Legacy source migration

The root `test` file is the original source and remains untouched for now.

Migration gate:

1. Parser regression tests pass against the original file.
2. Generated record count is recorded.
3. A byte-identical copy is created at `playlists/legacy.m3u`.
4. CI is updated to parse the new path and passes.
5. Only then may the root `test` file be removed in a separate commit.

This makes the move auditable and reversible.
