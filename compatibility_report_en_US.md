# Redis Major Version Compatibility Report

This document is compiled from the official Release Notes of the Redis community, insights from code reviews, and operational experience from the Alibaba Cloud Tair Team. It is intended to serve as a technical reference for Redis users to evaluate compatibility risks before undertaking major version upgrades. If you find any omissions, please open an issue to supplement this report. Accepted contributions will be acknowledged by adding your name to the list of contributors.

# User-Facing Compatibility Differences

## Upgrading from Version 4.0 to 5.0

1.  **`KEYS` Command Behavior:** The `KEYS` command no longer actively deletes expired keys it encounters during traversal; it only skips them. It can no longer be used as a mechanism for active expiration. The `SCAN` command, however, retains its behavior of deleting expired keys it finds.
    -   PR: [https://github.com/redis/redis/commit/edc47a3a](https://github.com/redis/redis/commit/edc47a3a)

2.  **Lua Script Replication:** Lua scripts now default to effect replication (replicating the resulting commands) instead of script replication. This change prevents data divergence between primary and replica instances. This behavior can be reverted by modifying the `lua-replicate-commands` configuration (removed in 7.0) or using the `DEBUG lua-always-replicate-commands` command.
    -   PR: [https://github.com/redis/redis/commit/3e1fb5ff](https://github.com/redis/redis/commit/3e1fb5ff)

    ```plaintext
    // 1. Non-deterministic commands can yield different results.
    local key = KEYS[1]
    local member = redis.call('SPOP', key)
    redis.call('SET', 'last_removed', member)
    return member

    // 2. Different execution paths due to expiration/eviction.
    local key = KEYS[1]
    local value = redis.call('GET', key)
    if value then
        redis.call('SET', key, tonumber(value) + 1)
    else
        redis.call('SET', key, 1)
    end
    ```

3.  **Read-only Script Replication:** Read-only scripts are now replicated as `SCRIPT LOAD` commands, not `EVAL`.
    -   PR: [https://github.com/redis/redis/commit/dfbce91a](https://github.com/redis/redis/commit/dfbce91a)

4.  **Replica `maxmemory` Policy:** Replicas now ignore the `maxmemory` setting by default and will not perform data eviction. The previous behavior can be restored by setting `replica-ignore-maxmemory` to `no`.
    -   PR: [https://github.com/redis/redis/commit/447da44d](https://github.com/redis/redis/commit/447da44d)

5.  **Shared Object Consistency:** When the `volatile-lru` eviction policy is active, Redis avoids using shared integer objects to ensure accurate LRU metadata. However, replicas loading an RDB file during a full sync did not apply this logic, resulting in the use of shared objects. This caused a memory representation mismatch where replicas consumed less memory than the primary for the same dataset. This has been fixed in Redis 5.0. After upgrading, you may observe that replica memory usage increases to match the primary's.
    -   MRs:
        -   [https://github.com/redis/redis/commit/bd92389c2dc1afcf53218880fc31ba45e66f4ded](https://github.com/redis/redis/commit/bd92389c2dc1afcf53218880fc31ba45e66f4ded)
        -   [https://github.com/redis/redis/commit/0ed0dc3c02dfffdf6bfb9e32f1335ddc34f37723](https://github.com/redis/redis/commit/0ed0dc3c02dfffdf6bfb9e32f1335ddc34f37723)

## Upgrading from Version 5.0 to 6.0

1.  **`OBJECT ENCODING` for Stream:** The `OBJECT ENCODING` command now correctly returns the encoding type for stream, instead of "unknown."
    -   PR: [https://github.com/redis/redis/pull/7797](https://github.com/redis/redis/pull/7797)

2.  **Read-only Transactions in Cluster:** In cluster mode, read-only transactions can now be executed on replicas instead of being redirected to the primary with a `MOVED` error.
    -   PR: [https://github.com/redis/redis/pull/7766](https://github.com/redis/redis/pull/7766)

    ```plaintext
    // Previous Behavior:
    connect to a replica in cluster
    > readonly
    > get k
    "v"
    > multi
    > get k
    > exec
    (error) MOVED

    // New Behavior:
    connect to a replica in cluster
    > readonly
    > get k
    "v"
    > multi
    > get k
    > exec
    "v"
    ```

3.  **Blocking Command Timeout Precision:** The `timeout` parameter for `BRPOP`, `BLPOP`, and `BRPOPLPUSH` was changed from an integer (seconds) to a float number (seconds). This introduced a bug where a timeout value less than or equal to 0.001 seconds was parsed as 0, causing an indefinite block. This bug was fixed in Redis 7.0.
    -   Docs: [https://redis.io/docs/latest/commands/brpop/](https://redis.io/docs/latest/commands/brpop/), [https://redis.io/docs/latest/commands/blpop/](https://redis.io/docs/latest/commands/blpop/), [https://redis.io/docs/latest/commands/brpoplpush/](https://redis.io/docs/latest/commands/brpoplpush/)

4.  **Blocking Pop Timeout Precision:** The `timeout` parameter for `BZPOPMIN` and `BZPOPMAX` was also changed from an integer to a float, introducing the same indefinite block bug for small timeout values, which was fixed in 7.0.
    -   Docs: [https://redis.io/docs/latest/commands/bzpopmin/](https://redis.io/docs/latest/commands/bzpopmin/), [https://redis.io/docs/latest/commands/bzpopmax/](https://redis.io/docs/latest/commands/bzpopmax/)

5.  **String Length Limits:** The maximum string size for `SETRANGE` and `APPEND` is now determined by the `proto_max_bulk_len` configuration (default 512MB), rather than a hardcoded 512MB limit.
    -   PR: [https://github.com/redis/redis/pull/4633](https://github.com/redis/redis/pull/4633)

## Upgrading from Version 6.0 to 6.2

1.  **AOF `fsync=always` Error Handling:** When `appendfsync` is set to `always`, a failed `fsync` operation will now cause the Redis process to terminate immediately.
    -   PR: [https://github.com/redis/redis/pull/8347](https://github.com/redis/redis/pull/8347)

2.  **Command Latency Statistics:** Latency statistics now include the time a command spends blocked, which affects `INFO commandstats`, `LATENCY` commands and `SLOWLOG` commands outputs.
    -   PR: [https://github.com/redis/redis/pull/7491](https://github.com/redis/redis/pull/7491)

3.  **`SRANDMEMBER` RESP3 Return Type:** The RESP3 return type for `SRANDMEMBER` has been changed from a Set to an Array to accommodate duplicate elements, which can be returned when a negative `count` is provided.
    -   PR: [https://github.com/redis/redis/pull/8504](https://github.com/redis/redis/pull/8504)

4.  **`PUBSUB NUMPAT` Return Value:** The meaning of the value returned by `PUBSUB NUMPAT` has changed. It now returns the count of unique subscribed patterns, whereas previously it returned the total number of subscribed clients for all patterns.
    -   PR: [https://github.com/redis/redis/pull/8472](https://github.com/redis/redis/pull/8472)
    -   Doc: [https://redis.io/docs/latest/commands/pubsub-numpat/](https://redis.io/docs/latest/commands/pubsub-numpat/)

5.  **`CLIENT TRACKING` with Overlapping Prefixes:** `CLIENT TRACKING` now returns an error if a client attempts to track overlapping prefixes, which prevents duplicate invalidation messages.
    -   PR: [https://github.com/redis/redis/pull/8176](https://github.com/redis/redis/pull/8176)

6.  **`SWAPDB` and `WATCH`:** The `SWAPDB` command now touches all keys being watched in both of the swapped databases, causing any transactions watching those keys to fail.
    -   PR: [https://github.com/redis/redis/pull/8239](https://github.com/redis/redis/pull/8239)

    ```plaintext
    // Previous Behavior: Transaction succeeds
    client A> select 0
    client A> set k 0
    client A> select 1
    client A[1]> set k 1
    client A[1]> watch k
    client A[1]> multi
    client A[1]> get k

    client B> swapdb 0 1

    client A[1]> exec
    "0"

    // New Behavior: Transaction fails
    client A> select 0
    client A> set k 0
    client A> select 1
    client A[1]> set k 1
    client A[1]> watch k
    client A[1]> multi
    client A[1]> get k

    client B> swapdb 0 1

    client A[1]> exec
    (nil)
    ```

7.  **`FLUSHDB` and Client Tracking:** `FLUSHDB` now invalidates all keys for all clients that have tracking enabled.
    -   PR: [https://github.com/redis/redis/pull/8039](https://github.com/redis/redis/pull/8039)

8.  **BIT ops Length Limit:** The maximum result size for bit ops is now controlled by `proto_max_bulk_len` (default 512MB), not a hardcoded 512MB limit.
    -   PR: [https://github.com/redis/redis/pull/8096](https://github.com/redis/redis/pull/8096)

9.  **`bind` Configuration Syntax:** A `-` prefix on an IP address in the `bind` directive now signifies that an `EADDRNOTAVAIL` error for that address should be ignored. Without the prefix, such an error on a non-default address will cause startup to fail. Additionally, `bind *` is now supported as an explicit way to bind to all available network interfaces.
    -   PR: [https://github.com/redis/redis/pull/7936](https://github.com/redis/redis/pull/7936)

    ```plaintext
    // Previous Behavior:
    Any bind failure was ignored as long as at least one succeeded.

    // New Behavior:
    Binding to the default address (127.0.0.1/::1) will not affect Redis startup if at least one address succeeds.
    Binding to a non-default address (e.g., -192.168.1.100) with a '-' prefix will not affect Redis startup if the address fails to bind. Failure to bind to the non-default address without the '-' prefix will cause Redis startup to fail.
    ```

10. **`save` Configuration with Command-Line Arguments:** Launching `redis-server` with parameters no longer resets the `save` configuration. Previously, using additional parameters, regardless of whether `save` was included, would cause the save configuration to be reset to "" before loading other additional parameters.
    -   PR: [https://github.com/redis/redis/pull/7092](https://github.com/redis/redis/pull/7092)

    ```plaintext
    // Previous Behavior:
    redis-server --other-args xx                   --> save ""
    redis-server [--other-args xx] --save 3600 1   --> save "3600 1"
    redis-server                                   --> save "3600 1 300 100 60 10000"

    // New Behavior:
    redis-server --other-args xx                   --> save "3600 1 300 100 60 10000"
    redis-server [--other-args xx] --save 3600 1   --> save "3600 1"
    redis-server                                   --> save "3600 1 300 100 60 10000"
    ```

11. **`SLOWLOG` Command Representation:** `SLOWLOG` now records the original command as executed by the client, not the rewritten version (e.g., `SPOP` is logged as `SPOP`, not `DEL`).
    -   PR: [https://github.com/redis/redis/pull/8006](https://github.com/redis/redis/pull/8006)

## Upgrading from Version 6.2 to 7.0

1.  **Lua Script Replication Finalized:** Lua scripts are definitively no longer persisted or replicated. The `SCRIPT LOAD` and `SCRIPT FLUSH` commands are also no longer replicated, and the `lua-replicate-commands` configuration has been removed. Effect replication is now the only mode.
    -   PR: [https://github.com/redis/redis/pull/9812](https://github.com/redis/redis/pull/9812)

2.  **Synchronous Shutdown:** A shutdown initiated by `SHUTDOWN`, `SIGTERM`, or `SIGINT` now waits for replicas to catch up on replication, with a timeout defined by `shutdown-timeout` (default 10 seconds).
    -   PR: [https://github.com/redis/redis/pull/9872](https://github.com/redis/redis/pull/9872)
    -   Command Doc: [https://redis.io/docs/latest/commands/shutdown/](https://redis.io/docs/latest/commands/shutdown/)

3.  **ACL Default Channel Permissions:** The default user's channel permissions have been changed from `allchannels` to `resetchannels`, effectively disabling all Pub/Sub commands by default until explicitly permitted.
    -   PR: [https://github.com/redis/redis/pull/10181](https://github.com/redis/redis/pull/10181)

4.  **`ACL LOAD` with Duplicate Users:** `ACL LOAD` now returns an error if the loaded configuration contains duplicate user definitions, instead of silently applying the last one.
    -   PR: [https://github.com/redis/redis/pull/9330](https://github.com/redis/redis/pull/9330)

5.  **Expiration Replication:** Key expiration times are now always replicated as absolute millisecond-precision timestamps.
    -   PR: [https://github.com/redis/redis/pull/8474](https://github.com/redis/redis/pull/8474)

6.  **`STRALGO` Command Removed:** The `STRALGO` command has been removed and its functionality promoted to the top-level `LCS` command.
    -   PR: [https://github.com/redis/redis/pull/9799](https://github.com/redis/redis/pull/9799)
    -   Doc: [https://redis.io/docs/latest/commands/lcs/](https://redis.io/docs/latest/commands/lcs/)

7.  **New Security Configuration:** Three new immutable startup configurations have been added: `enable-protected-configs`, `enable-debug-command`, and `enable-module-command`. All default to `no`, providing a more secure-by-default posture by disabling runtime changes to protected configs and access to `DEBUG` and `MODULE` commands.
    -   PR: [https://github.com/redis/redis/pull/9920](https://github.com/redis/redis/pull/9920)

8.  **Transaction Command Restrictions:** `SAVE`, `PSYNC`, `SYNC`, and `SHUTDOWN` are now prohibited inside a `MULTI`/`EXEC` block. `BGSAVE`, `BGREWRITEAOF`, and `CONFIG SET appendonly` are deferred until after the transaction executes.
    -   PR: [https://github.com/redis/redis/pull/10015](https://github.com/redis/redis/pull/10015)

9.  **`ZPOPMIN`/`ZPOPMAX` Error Handling:** These commands now return a `WRONGTYPE` error for non-sorted-set keys and an error for a negative `count`, instead of returning an empty array.
    -   PR: [https://github.com/redis/redis/pull/9711](https://github.com/redis/redis/pull/9711)

10. **`CONFIG REWRITE` and Modules:** `CONFIG REWRITE` now persists currently loaded modules to the configuration file using `loadmodule` directives.
    -   PR: [https://github.com/redis/redis/pull/4848](https://github.com/redis/redis/pull/4848)

11. **`X[AUTO]CLAIM` for Deleted Messages:** `XCLAIM` and `XAUTOCLAIM` now handle cases where a pending message has been deleted from the stream. Instead of returning `nil`, they now remove the message from the Pending Entries List (PEL). `XAUTOCLAIM` also returns a list of deleted message IDs.
    -   PR: [https://github.com/redis/redis/pull/10227](https://github.com/redis/redis/pull/10227)
    -   Docs: [https://redis.io/docs/latest/commands/xclaim/](https://redis.io/docs/latest/commands/xclaim/), [https://redis.io/docs/latest/commands/xautoclaim/](https://redis.io/docs/latest/commands/xautoclaim/)

    ```plaintext
    // Previous Behavior:
    > XADD x 1 f1 v1
    "1-0"
    > XADD x 2 f1 v1
    "2-0"
    > XADD x 3 f1 v1
    "3-0"
    > XGROUP CREATE x grp 0
    OK
    > XREADGROUP GROUP grp Alice COUNT 2 STREAMS x >
    1) 1) "x"
       2) 1) 1) "1-0"
             2) 1) "f1"
                2) "v1"
          2) 1) "2-0"
             2) 1) "f1"
                2) "v1"
    > XDEL x 1 2
    (integer) 2
    > XCLAIM x grp Bob 0 0-99 1-0 1-99 2-0
    1) (nil)
    2) (nil)
    > XPENDING x grp
    1) (integer) 2
    2) "1-0"
    3) "2-0"
    4) 1) 1) "Bob"
          2) "2"

    // New Behavior:
    > Same until XDEL
    > XCLAIM x grp Bob 0 0-99 1-0 1-99 2-0
    (empty array)
    > XPENDING x grp
    1) (integer) 0
    2) (nil)
    3) (nil)
    4) (nil)
    ```

12. **`XREADGROUP` Unblocking:** A client blocked on `XREADGROUP` will now be unblocked if the target stream key is deleted.
    -   PR: [https://github.com/redis/redis/pull/10306](https://github.com/redis/redis/pull/10306)

13. **`SORT` with `BY`/`GET` Permissions:** `SORT` and `SORT_RO` now require read permissions for all external keys referenced via `BY` or `GET` patterns.
    -   PR: [https://github.com/redis/redis/pull/10340](https://github.com/redis/redis/pull/10340)

14. **Replica Persistence Errors:** A replica will now panic and exit if it fails to do persistence operations, preventing it from continuing with a potentially diverged dataset. Set `replica-ignore-disk-write-errors yes` to restore the old behavior (default is no).
    -   PR: [https://github.com/redis/redis/pull/10504](https://github.com/redis/redis/pull/10504)

15. **Lua `print` Function Removed:** The `print()` function in Lua scripts is removed. Use `redis.log(...)` for logging.
    -   PR: [https://github.com/redis/redis/pull/10651](https://github.com/redis/redis/pull/10651)

16. **Read-only Script Command Restrictions:** `PFCOUNT` and `PUBLISH` are now disallowed in read-only scripts, as they can have side effects that must be replicated.
    -   PR: [https://github.com/redis/redis/pull/10744](https://github.com/redis/redis/pull/10744)

17. **Subcommand Statistics:** Command statistics are now tracked at the subcommand level. For example, `INFO commandstats` will show separate entries for `CLIENT LIST` and `CLIENT TRACKING` instead of a single entry for `CLIENT`.
    -   PR: [https://github.com/redis/redis/pull/9504](https://github.com/redis/redis/pull/9504)

18. **Multi-Part AOF:** A new AOF format has been introduced. The AOF is now stored as a directory (path configured by `appenddirname`) containing a manifest, a base AOF file, and incremental AOF files.
    -   PR: [https://github.com/redis/redis/pull/9788](https://github.com/redis/redis/pull/9788)

## Upgrading from Version 7.0 to 7.2

1.  **Client Tracking in Lua Scripts:** When Client Tracking is enabled, tracking is now based on the keys actually accessed by commands within a Lua script, rather than all keys declared in the `EVAL` call.
    -   PR: [https://github.com/redis/redis/pull/11770](https://github.com/redis/redis/pull/11770)

    ```plaintext
    // Previous Behavior: Tracks all declared keys
    client A> CLIENT TRACKING on
    client A> EVAL "redis.call('get', 'key2')" 2 key1 key2

    client B> MSET key1 1 key2 2

    client A> -> invalidate: 'key1'
    client A> -> invalidate: 'key2'

    // New Behavior: Tracks only accessed keys
    client A> CLIENT TRACKING on
    client A> EVAL "redis.call('get', 'key2')" 2 key1 key2

    client B> MSET key1 1 key2 2

    client A> -> invalidate: 'key2'
    ```

2.  **Time Caching within Commands:** Command execution now uses a "time snapshot." The server time is cached at the beginning of a command's execution (or a Lua script) and remains constant throughout. A typical example is that you cannot wait for a key to expire in a Lua script.
    -   PR: [https://github.com/redis/redis/pull/10300](https://github.com/redis/redis/pull/10300)

3.  **ACL Verbosity:** ACL now records all permission modifications, even redundant ones. This affects the output of `ACL SAVE`, `ACL GETUSER`, and `ACL LIST`.
    -   PR: [https://github.com/redis/redis/pull/11224](https://github.com/redis/redis/pull/11224)

4.  **Stream Consumer Creation:** `XREADGROUP` and `X[AUTO]CLAIM` now create a consumer in the consumer group even if no messages are successfully read or claimed.
    -   PR: [https://github.com/redis/redis/pull/11099](https://github.com/redis/redis/pull/11099)

5.  **Stream Consumer Idle Time:** When the XREADGROUP command does not read any message, it resets the idle field of the consumer and adds the active-time field to record the time when the consumer last successfully read a message.
    -   PR: [https://github.com/redis/redis/pull/11099](https://github.com/redis/redis/pull/11099)

6.  **Re-checking on Unblocking:** When a client unblocks from a blocking command, security and resource limit checks (e.g., ACL, OOM) are performed again before the command proceeds.
    -   PR: [https://github.com/redis/redis/pull/11012](https://github.com/redis/redis/pull/11012)

    ```plaintext
    // Previous Behavior:
    // Check ACL/OOM -> Block -> Unblock -> Execute

    // New Behavior:
    // Check ACL/OOM -> Block -> Unblock -> Re-check ACL/OOM -> Execute
    ```

# Important Bugfixes

## Version 5.0

1.  **UAF Crash on Key Expiration:** Fixed a critical Use-After-Free (UAF) vulnerability where a key could expire and be deleted during command execution, leading to a server crash. (Affects 4.0 and earlier)
    -   PR: [https://github.com/redis/redis/commit/68d71d83](https://github.com/redis/redis/commit/68d71d83)

2.  **AOF `everysec` Data Loss:** Fixed a bug when the AOF flushing policy is set to everysec, data within the last second may not be flushed to disk, resulting in data loss. (Affects 4.0 and earlier)
    -   PR: [https://github.com/redis/redis/commit/c6b1252f](https://github.com/redis/redis/commit/c6b1252f)

3.  **Transaction Error Stats:** Fixed a bug where errors from commands within a transaction were incorrectly attributed to the `EXEC` command in command statistics. (Affects 4.0 and earlier)
    -   PR: [https://github.com/redis/redis/commit/d6aeca86](https://github.com/redis/redis/commit/d6aeca86)

## Version 6.0

1.  **`KEYS` Pattern with Null Byte:** Fixed a bug where a `KEYS` pattern starting with `\*\0` would match all keys in the database. (Backported to 5.0; affects 4.0 and earlier)
    -   PR: [https://github.com/redis/redis/commit/c7f75266](https://github.com/redis/redis/commit/c7f75266)

2.  **Float Conversion with Null Byte:** String-to-float conversions now correctly fail if the string contains a null byte (`\0`). This affects commands like `HINCRBYFLOAT`. (Affects 5.0 and earlier)
    -   PR: [https://github.com/redis/redis/commit/6fe55c2f](https://github.com/redis/redis/commit/6fe55c2f)

3.  **`-READONLY` Error in Transactions:** A `-READONLY` error within a transaction now correctly aborts the transaction. (Affects 5.0 and earlier)
    -   PR: [https://github.com/redis/redis/commit/8783304a](https://github.com/redis/redis/commit/8783304a)

## Version 6.2

1.  **`EXISTS`/`OBJECT` and LRU:** `EXISTS` no longer modifies a key's LRU value, and `OBJECT` no longer returns information for expired keys. (Backported to 6.0; affects 5.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/8016](https://github.com/redis/redis/pull/8016)

2.  **Hash Table Sampling Fairness:** Fixed a 32-bit limitation in random element sampling from hash tables, which impacted the fairness of eviction and commands like `RANDOMKEY` and `SRANDMEMBER` on large hashes. (Backported to 6.0; affects 5.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/8133](https://github.com/redis/redis/pull/8133)

3.  **`SMOVE` Notifications:** `SMOVE` no longer generates `WATCH` or `CLIENT TRACKING` notifications if the move is a no-op. (Backported to 6.0; affects 5.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/9244](https://github.com/redis/redis/pull/9244)

4.  **Pipeline Stall after Lua Timeout:** Fixed an issue where a timed-out Lua script in a pipeline could cause the server to stop processing subsequent commands from that client until new data arrived. (Affects 6.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/8715](https://github.com/redis/redis/pull/8715)

5.  **`SCRIPT KILL` and `pcall`:** `SCRIPT KILL` can now successfully terminate a script that is inside a `pcall` block. (Affects 6.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/8661](https://github.com/redis/redis/pull/8661)


## Version 7.0

1.  **Lua Stack Overflow:** Fixed an assertion failure caused by a stack overflow when passing an extremely large number of arguments to a Lua script. (Backported to 6.0; affects 5.0)
    -   PR: [https://github.com/redis/redis/pull/9809](https://github.com/redis/redis/pull/9809)

2.  **`list-compress-depth` Crash:** Fixed a potential crash when using the `list-compress-depth` configuration. (Affects 6.2 and earlier)
    -   PR: [https://github.com/redis/redis/pull/9849](https://github.com/redis/redis/pull/9849)

3.  **RDB Corruption with Large Items:** Fixed RDB file corruption when `rdbcompression` is enabled and the RDB contains a String or List value larger than 4GB. (Affects 6.2 and earlier)
    -   PR: [https://github.com/redis/redis/pull/9776](https://github.com/redis/redis/pull/9776)

4.  **Crash on Large Set/Hash Elements:** Fixed a crash when adding an element larger than 2GB to a Set or Hash. (Affects 6.2 and earlier)
    -   PR: [https://github.com/redis/redis/pull/9916](https://github.com/redis/redis/pull/9916)

5.  **Expiration Time Overflow:** Setting an extremely large or small expiration time now returns an error instead of causing an integer overflow. (Backported to 6.2; affects 6.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/8287](https://github.com/redis/redis/pull/8287)

6.  **`DECRBY` with `LLONG_MIN`:** `DECRBY` now returns an error when the decrement value is `LLONG_MIN`, preventing an integer overflow. (Affects 6.2 and earlier)
    -   PR: [https://github.com/redis/redis/pull/9577](https://github.com/redis/redis/pull/9577)

7.  **ZSet Rank Overflow:** Fixed a potential rank calculation overflow in sorted sets with more than `UINT32_MAX` elements. (Affects 6.2 and earlier)
    -   PR: [https://github.com/redis/redis/pull/9249](https://github.com/redis/redis/pull/9249)

8.  **Lua and `CLIENT TRACKING NOLOOP`:** Fixed a bug where write commands executed within a Lua script would ignore the `CLIENT TRACKING NOLOOP` option. (Affects 6.0)
    -   PR: [https://github.com/redis/redis/pull/11052](https://github.com/redis/redis/pull/11052)

9.  **`CLIENT TRACKING` Message Interleaving:** Fixed a bug where client tracking invalidation messages could be interleaved with the replies of other commands on the same connection. (Backported to 6.2; affects 6.0)
    -   PRs: [https://github.com/redis/redis/pull/11038](https://github.com/redis/redis/pull/11038), [https://github.com/redis/redis/pull/9422](https://github.com/redis/redis/pull/9422)

10. **`WATCH` and Expired Keys:** A transaction now fails if a `WATCH`ed key has expired by the time of `EXEC`, regardless of whether it has been actively deleted. In addition, during the execution of a transaction, the timestamp used by the server to determine whether it has expired should not be updated. (Backported to 6.0; affects 5.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/9194](https://github.com/redis/redis/pull/9194)

11. **`SINTERSTORE` Type Errors:** Fixed a bug where `SINTERSTORE` failed to return a `WRONGTYPE` error and could delete the destination key when operating on incorrect types. (Backported to 6.0; affects 5.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/9032](https://github.com/redis/redis/pull/9032)

12. **Client Buffer Soft Limit Timeout:** Fixed a bug where a client exceeding a `client-output-buffer-limit` soft limit would not be disconnected after the timeout if it remained idle. (Backported to 6.2; affects 6.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/8833](https://github.com/redis/redis/pull/8833)

13. **Stream Keyspace Notifications:** Fixed bugs where stream commands for consumer management did not emit or incorrectly emitted keyspace notifications. (Affects 6.2 and earlier)
    -   PR: [https://github.com/redis/redis/pull/9263](https://github.com/redis/redis/pull/9263)

14. **`GEO` Search Boundary Bug:** Fixed a bug in `GEO` search commands that could cause them to miss elements located very close to the search radius boundary. (Affects 6.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/10018](https://github.com/redis/redis/pull/10018)

15. **Lua Metatable Error Crash:** Fixed a server crash that could occur if an error was triggered while processing a Lua return value that involved a metatable. (Affects 6.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/11032](https://github.com/redis/redis/pull/11032)

16. **Blocking Command Indefinite Block:** Fixed the bug where blocking commands with timeouts could block indefinitely if the timeout was less than 0.001 seconds. (Affects 6.2 and earlier)
    -   PR: [https://github.com/redis/redis/pull/11688](https://github.com/redis/redis/pull/11688)

17. **Denial of Service via Random Commands:** Fixed vulnerabilities where maliciously crafted `KEYS`, `HRANDFIELD`, `SRANDMEMBER`, and `ZRANDMEMBER` commands could cause the server to hang. (`KEYS` may still causes a hang in 6.2 and earlier)
    -   PR: [https://github.com/redis/redis/pull/11676](https://github.com/redis/redis/pull/11676)

18. **Lua Readonly Table:** As a security enhancement, prohibiting modification of existing global variables and standard library functions.(Backported to 6.2; affects 6.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/10651](https://github.com/redis/redis/pull/10651)

## Version 7.2

1.  **Random Command Infinite Loop:** Fixed a bug in `SRANDMEMBER`, `ZRANDMEMBER`, and `HRANDFIELD` where using the `count` argument had a small probability of causing an infinite loop. (Backported to 7.0; affects 6.2 and earlier)
    -   PR: [https://github.com/redis/redis/pull/12276](https://github.com/redis/redis/pull/12276)

2.  **`HINCRBYFLOAT` Key Creation:** `HINCRBYFLOAT` no longer creates a hash key if the `increment` argument is not a valid float. (Backported to 6.0; affects 5.0 and earlier)
    -   PR: [https://github.com/redis/redis/pull/11149](https://github.com/redis/redis/pull/11149)
    -   Doc: [https://redis.io/docs/latest/commands/hincrbyfloat/](https://redis.io/docs/latest/commands/hincrbyfloat/)

3.  **`LSET` Crash on Large Element Replacement:** Fixed a potential crash with `LSET` in extreme cases when replacing many small list elements with a large one. (Affects 7.0)
    -   PR: [https://github.com/redis/redis/pull/12955](https://github.com/redis/redis/pull/12955)
    -   Doc: [https://redis.io/docs/latest/commands/lset/](https://redis.io/docs/latest/commands/lset/)