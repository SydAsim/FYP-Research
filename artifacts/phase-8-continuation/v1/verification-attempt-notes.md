# Verification attempts

All tests here are offline controls; none invokes a scientific driver or AWS write.
Earlier test-collection, lint and type-check failures are retained as numbered logs.
The Windows SDK-path attempt mistakenly type-checked third-party SDK internals;
its 8,021 reported errors are retained. No library was upgraded to suppress them.

The initial Linux command passed 11 then-current tests in 9.87 seconds, but mypy
1.20.2 returned an internal error. Restarting that same offline container reused
its output filenames; this was a recording error. The first terminal result is
recovered verbatim below, separately identified as recovered terminal output.
The second command output is preserved in `offline-repeat-attempt2.txt`.
No scientific execution, observation, frozen artifact or outcome was overwritten.

```text
...........                                                              [100%]
11 passed in 9.87s
error: INTERNAL ERROR -- Please try using mypy master on GitHub:
https://mypy.readthedocs.io/en/stable/common_issues.html#using-a-development-mypy-build
If this issue continues with mypy master, please report a bug at https://github.com/python/mypy/issues
version: 1.20.2
note: please use --show-traceback to print a traceback when reporting a bug
```

A separate offline container, separate output paths and fresh `/tmp` mypy cache
then passed 19 tests and strict type checking of 13 files. The writable cache
avoids the read-only cross-platform cache failure. Subsequent final checks use
new numbered output paths. Synthetic signed controls live only in temporary
test directories and cannot constitute human acceptance, freezing or launching.
