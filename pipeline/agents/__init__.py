"""Pipeline agent layers. Each module = one layer's prompt + runner + validator
(see ARCHITECTURE.md). Layers read the previous artifact and write their own;
none call another layer directly, so each can be re-run in isolation."""
