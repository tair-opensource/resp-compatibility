#!/usr/bin/env python3
import argparse
import redis
import json
from dataclasses import dataclass
from typing import List, Dict

EXAMPLE = """
Examples:

Run tests without specifying a version
    python3 redis_compatibility_test.py --testfile cts.json

Run the test for compatibility with Redis 6.2.0
    python3 redis_compatibility_test.py --testfile cts.json --specific-version 6.2.0

Run the test whether it is compatible with Redis 6.2.0, and print the failure case
    python3 redis_compatibility_test.py --testfile cts.json --specific-version 6.2.0 --show-failed
"""


@dataclass
class FailedTest:
    name: str
    reason: object


@dataclass
class TestResult:
    total: int
    passed: int
    failed: List[FailedTest]


r: redis.Redis = None
g_results: Dict[str, TestResult] = {}


def report_result():
    print(f"-------- The result of tests --------")
    if args.specific_version:
        total = passed = 0
        failed: List[FailedTest] = []
        for v, t in g_results.items():
            total += t.total
            passed += t.passed
            failed.extend(t.failed)
        print(f"version: {args.specific_version}, total tests: {total}, passed: {passed}, "
              f"rate: {repr(passed / total * 100)}%")
        if args.show_failed and len(failed) != 0:
            print(f"This is failed tests for {args.specific_version}:")
            print(failed)
    else:
        for v, t in sorted(g_results.items()):
            print(f"version: {v}, total tests: {t.total}, passed: {t.passed}, "
                  f"rate: {repr(t.passed / t.total * 100)}%")
            if args.show_failed and len(t.failed) != 0:
                print(f"This is failed tests for {v}:")
                print(t.failed)


def is_equal(left, right):
    if type(left) is bytes and type(right) is str:
        return left.decode() == right
    elif type(left) is str and type(right) is bytes:
        return left == right.decode()
    else:
        return left == right


def test_passed(result):
    print("passed")
    result.total += 1
    result.passed += 1


def test_failed(result, name, e):
    print("failed")
    result.total += 1
    result.failed.append(FailedTest(name=name, reason=e))


def trans_result_to_bytes(result):
    if type(result) is str:
        return result.encode()
    if type(result) is list:
        for i in range(len(result)):
            result[i] = trans_result_to_bytes(result[i])
    if type(result) is map:
        for k, v in result.items():
            result[k.encode()] = trans_result_to_bytes(v)
            del result[k]
    return result


def trans_cmd(test, cmd):
    if 'command_binary' in test:
        array = bytearray()
        i = 0
        while i < len(cmd):
            if cmd[i] == '\\' and cmd[i + 1] == '\\':
                array.append(92)
                i += 2
            elif cmd[i] == '\\' and cmd[i + 1] == '"':
                array.append(34)
                i += 2
            elif cmd[i] == '\\' and cmd[i + 1] == 'n':
                array.append(10)
                i += 2
            elif cmd[i] == '\\' and cmd[i + 1] == 'r':
                array.append(13)
                i += 2
            elif cmd[i] == '\\' and cmd[i + 1] == 't':
                array.append(9)
                i += 2
            elif cmd[i] == '\\' and cmd[i + 1] == 'a':
                array.append(7)
                i += 2
            elif cmd[i] == '\\' and cmd[i + 1] == 'b':
                array.append(8)
                i += 2
            elif cmd[i] == '\\' and cmd[i + 1] == 'x':
                array.append(int(cmd[i + 2], 16) * 16 + int(cmd[i + 3], 16))
                i += 4
            else:
                array.append(ord(cmd[i]))
                i += 1
        return bytes(array)
    else:
        return cmd


def run_test(test):
    name = test['name']
    print(f"test: {name}", end=" ")
    # if test need skipped
    if 'skipped' in test:
        print("skipped")
        return

    # high version test
    since = test['since']
    if args.specific_version and since > args.specific_version:
        print("version skipped")
        return
    if since not in g_results:
        g_results[since] = TestResult(total=0, passed=0, failed=[])

    r.flushall()
    command = test['command']
    result = test['result']
    trans_result_to_bytes(result)
    try:
        for idx, cmd in enumerate(command):
            ret = r.execute_command(trans_cmd(test, cmd))
            if result[idx] != ret:
                test_failed(g_results[since], name, f"expected: {result[idx]}, result: {ret}")
                return
        test_passed(g_results[since])
    except Exception as e:
        test_failed(g_results[since], name, e)


def run_compatibility_tests(filename):
    with open(filename, "r") as f:
        tests = f.read()
    tests_array = json.loads(tests)
    for test in tests_array:
        run_test(test)


def create_client(args):
    global r
    if args.cluster:
        print(f"Connecting to {args.host}:{args.port} use cluster client")
        r = redis.RedisCluster(host=args.host, port=args.port, password=args.password, ssl=args.ssl)
        assert r.ping()
    else:
        print(f"Connecting to {args.host}:{args.port} use standalone client")
        r = redis.Redis(host=args.host, port=args.port, password=args.password, ssl=args.ssl)
        assert r.ping()


def parse_args():
    parser = argparse.ArgumentParser(prog="redis_compatibility_test",
                                     description="redis_compatibility_test is used to test whether your redis-like "
                                                 "database is compatible with Redis versions (such as 6.0, 7.0, etc.)",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=EXAMPLE)
    parser.add_argument("--host", help="the redis host", default="127.0.0.1")
    parser.add_argument("--port", help="the redis port", default=6379, type=int)
    parser.add_argument("--password", help="the redis password", default="")
    parser.add_argument("--testfile", help="the redis compatibility test cases", required=True)
    parser.add_argument("--specific-version", dest="specific_version", help="the redis version",
                        choices=['1.0.0', '2.8.0', '4.0.0', '5.0.0', '6.0.0', '6.2.0', '7.0.0'])
    parser.add_argument("--show-failed", dest="show_failed", help="show details of failed tests", default=False,
                        action="store_true")
    parser.add_argument("--cluster", help="server is a node of the Redis cluster", default=False, action="store_true")
    parser.add_argument("--ssl", help="open ssl connection", default=False, action="store_true")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    create_client(args)
    run_compatibility_tests(args.testfile)
    report_result()
