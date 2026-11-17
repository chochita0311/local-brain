# SPEC-0171: Native Terminal Integration

- Status: `approved`
- Feature: [FEAT-0171](../feature/feat-0171-native-terminal-integration.md)
- Run: [Run252](../run/run-20261113-252-native-terminal-integration.md)
- Profile: `fullstack-product`; contract/backend→native/frontend→infra/integration/docs.

Implement FEAT0170 as the one runtime, under the selected immutable-payload/scope/
helper/lease/loss contract. Bundle terminal resources outside the Python backend,
provide their absolute trusted path from Tauri, and copy final verified bytes only
on explicit prepare/start/create. Current shared data/cache formula remains.

Enable only Terminal in desktop feature selection/allowlist, include its Python
adapter and UI/fonts/checkpoint assets. WS checks the same per-launch cookie/token
and exact Host/Origin before spawning Rust or accepting; HTTP middleware alone is
insufficient. Do not forward desktop secrets to Node/shell/helper.

Native close hides; Quit stops the app backend and stream children only. Payload
manager/helper/cache launcher remain stable and outlive source app/backend paths.
Explicit service stop/update verifies generation, exact IDs, PID/birth and socket
exit; failure never permits a second owner. Default app update requires users to
finish affected work; no automatic kill/replay/login service is introduced.

Use current pinned engine and Node24.15.0 darwin-arm64 verified official artifact,
ad-hoc sign Mach-O code before manifest hashing, preserve licenses. Cache modes
0600/0700 and strict sorted manifest/hash/ABI/full-scope metadata are validated.
Actual installed-app smoke uses synthetic data and relocated bundle, never the
user's active jobs/settings. Report actual platform/performance gaps separately.
