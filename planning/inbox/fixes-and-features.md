
# ctrl-c broken

when running `pigeon start`, the command repsonds to ctrl-c but it doesn't end up stopping.  please fix.

```
^C2026-02-01 20:40:07,259 - pigeon.poller - INFO - Received signal 2, shutting down gracefully
2026-02-01 20:40:07,259 - pigeon.poller - INFO - Stopping Pigeon poller
2026-02-01 20:40:07,260 - pigeon.poller - INFO - Saved state with 1 tracked files
^C2026-02-01 20:40:07,449 - pigeon.poller - INFO - Received signal 2, shutting down gracefully
2026-02-01 20:40:07,449 - pigeon.poller - INFO - Stopping Pigeon poller
2026-02-01 20:40:07,450 - pigeon.poller - INFO - Saved state with 1 tracked files
```

# --keep-remote

By default, when a file is successfully written with timestamp to inbox, delete
the remote file unless --keep-remote.



