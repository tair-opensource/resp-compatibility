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
  --specific-version {1.0.0,2.8.0,3.2.0,4.0.0,5.0.0,6.0.0,6.2.0,7.0.0,7.2.0}
                        the redis version
  --show-failed         show details of failed tests
  --cluster             server is a node of the Redis cluster
  --ssl                 open ssl connection
  --genhtml             generate test report in html format
```
e.g. Test whether host:port is compatible with redis 6.2.0 and display failure case: 
```
$ python3 redis_compatibility_test.py -h host -p port --testfile cts.json --specific-version 6.2.0 --show-failed
Connecting to 127.0.0.1:6379 use standalone client
test: del command passed
test: unlink command passed
...
test: xtrim command with MINID/LIMIT passed
-------- The result of tests --------
Summary: version: 6.2.0, total tests: 285, passed: 285, rate: 100.00%
```
More examples are shown `python3 redis_compatibility_test.py -h`.

## cluster
Redis has two modes from the API level, namely `Standalone` (Sentinel has no API restrictions like Standalone) and `Cluster`, where the command support of Standalone does not require Cross slot, but Cluster restricts multi-key commands to be executed in the same slot (e.g. mset/mget ), therefore, we support `--cluster` to test the compatibility of cluster mode, you can test your Redis Cluster cluster compatibility as follows:
```
$ python3.9 redis_compatibility_test.py --testfile cts.json --host 127.0.0.1 --port 30001 --cluster --specific-version 6.2.0
connecting to 127.0.0.1:30001 use cluster client
test: del command passed
test: unlink command passed
...
test: xtrim command with MINID/LIMIT passed
-------- The result of tests --------
Summary: version: 6.2.0, total tests: 260, passed: 260, rate: 100.00%
```

## genhtml
You can use `--genhtml` to generate a test report similar to the html of this [website](https://tair-opensource.github.io/compatibility-test-suite-for-redis/). It should be noted that this option will read the configuration in [config.yaml](config.yaml) for testing. Special attention needs to be paid, at this time the `specific-version` specified in your command line will be overwritten by the one in the configuration file.
```
$ python3.9 redis_compatibility_test.py --testfile cts.json --genhtml --show-failed
directory html already exists, will be deleted and renewed.
start test Redis for version 4.0.0
connecting to 127.0.0.1:6379 using standalone client
start test Redis for version 5.0.0
connecting to 127.0.0.1:6379 using standalone client
start test Redis for version 6.0.0
connecting to 127.0.0.1:6379 using standalone client
start test Redis for version 7.0.0
connecting to 127.0.0.1:6379 using standalone client
...
Visit http://localhost:8000 for the report.
```
Then, an Http Server will be started on http://localhost:8000 by default, and you can access it to get reports.