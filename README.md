# compatibility-test-suite-for-redis

[![4.0](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/4.0.yaml/badge.svg)](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/4.0.yaml) [![5.0](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/5.0.yaml/badge.svg)](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/5.0.yaml) [![6.0](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/6.0.yaml/badge.svg)](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/6.0.yaml) [![6.2](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/6.2.yaml/badge.svg)](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/6.2.yaml) [![7.0](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/7.0.yaml/badge.svg)](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/7.0.yaml) [![7.2](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/7.2.yaml/badge.svg)](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/7.2.yaml) [![unstable](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/unstable.yaml/badge.svg)](https://github.com/tair-opensource/compatibility-test-suite-for-redis/actions/workflows/unstable.yaml)

compatibility-test-suite-for-redis is used to test whether your redis-like database is compatible with Redis versions (such as
6.0, 7.0, etc.)

# Install

requires `Python 3.7` or later.

```
pip3 install -r requirements.txt
```

# How to use

```
optional arguments:
  -h, --help            show this help message and exit
  --host HOST           the redis host
  --port PORT           the redis port
  --password PASSWORD   the redis password
  --testfile TESTFILE   the redis compatibility test cases
  --specific-version {1.0.0,2.8.0,4.0.0,5.0.0,6.0.0,6.2.0,7.0.0}
                        the redis version
  --show-failed         show details of failed tests
  --cluster             server is a node of the Redis cluster
  --ssl                 open ssl connection
```

Examples:  
Test whether host:port is compatible with redis 6.2.0 and display failure case: 
```
$ python3 redis_compatibility_test.py -h host -p port --testfile cts.json --specific-version 6.2.0 --show-failed
test: pexpiretime command version skipped
test: persist command passed
...
test: set command passed
-------- The result of tests --------
version: 6.2.0, total tests: 17, passed: 17, rate: 100.0%
```
More examples are shown `python3 redis_compatibility_test.py -h`.