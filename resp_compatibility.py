#!/usr/bin/env python3
import argparse
import os
import re
import http.server

import redis
import json
import yaml
import shutil
import datetime
from dataclasses import dataclass
from typing import List, Dict

EXAMPLE = """
Examples:

Run tests without specifying a version
    python3  resp_compatibility.py --testfile cts.json

Run the test for compatibility with Redis 6.2.0
    python3  resp_compatibility.py --testfile cts.json --specific-version 6.2.0

Run the test whether it is compatible with Redis 6.2.0, and print the failure case
    python3  resp_compatibility.py --testfile cts.json --specific-version 6.2.0 --show-failed
    
Run the test for redis cluster
    python3  resp_compatibility.py --testfile cts.json --host 127.0.0.1 --port 30001 --cluster
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
logfile = None


def report_result():
    print(f"-------- The result of tests --------", file=logfile)
    if args.specific_version:
        total = passed = 0
        failed: List[FailedTest] = []
        for v, t in g_results.items():
            total += t.total
            passed += t.passed
            failed.extend(t.failed)
        rate = passed / total * 100
        print(f"Summary: version: {args.specific_version}, total tests: {total}, passed: {passed}, "
              f"rate: {rate:.2f}%", file=logfile)
        if args.show_failed and len(failed) != 0:
            print(f"This is failed tests for {args.specific_version}:", file=logfile)
            print('\n'.join(str(fail) for fail in failed), file=logfile)
    else:
        for v, t in sorted(g_results.items()):
            rate = t.passed / t.total * 100
            print(f"Summary: version: {v}, total tests: {t.total}, passed: {t.passed}, "
                  f"rate: {rate:.2f}%", file=logfile)
        for v, t in sorted(g_results.items()):
            if args.show_failed and len(t.failed) != 0:
                print(f"This is failed tests for {v}:", file=logfile)
                print('\n'.join(str(fail) for fail in t.failed), file=logfile)


def test_passed(result):
    print("passed", file=logfile)
    result.total += 1
    result.passed += 1


def test_failed(result, name, e):
    print("failed", file=logfile)
    result.total += 1
    result.failed.append(FailedTest(name=name, reason=e))


def trans_cmd_to_binary(cmd):
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


def split_cmd_as_list(cmd, command_binary):
    # split command by ""
    # input: 'hello "world of python" example'
    # output: ['hello', 'world of python', 'example']
    parts = []
    in_quote = False
    current_part = b'' if command_binary else ''
    for char in cmd:
        byte = char if command_binary else ord(char)
        if byte == ord('"'):
            in_quote = not in_quote
        elif byte == ord(' ') and not in_quote:
            parts.append(current_part)
            current_part = b'' if command_binary else ''
        else:
            if command_binary:
                current_part += bytes([byte])
            else:
                current_part += char
    parts.append(current_part)
    if command_binary:
        parts[0] = parts[0].decode()
    return parts


def sort_nested_list(result):
    has_nested_list = False
    for i in range(len(result)):
        if isinstance(result[i], list):
            has_nested_list = True
            result[i] = sort_nested_list(result[i])
    if has_nested_list:
        return result
    else:
        return sorted(result)


def run_test(test):
    name = test['name']
    print(f"test: {name}", end=" ", file=logfile)
    # if test need skipped
    if 'skipped' in test:
        print("skipped", file=logfile)
        return

    # judge tags not match
    if 'tags' in test:
        tags = test['tags']
        if (args.cluster and tags == "standalone") or \
                (not args.cluster and tags == "cluster"):
            print("tags skipped", file=logfile)
            return

    # high version test
    since = test['since']
    if args.specific_version and since > args.specific_version:
        print("version skipped", file=logfile)
        return
    if since not in g_results:
        g_results[since] = TestResult(total=0, passed=0, failed=[])

    r.flushall()
    command = test['command']
    result = test['result']
    try:
        for idx, cmd in enumerate(command):
            if 'command_binary' in test:
                cmd = trans_cmd_to_binary(cmd)
                tcmd = split_cmd_as_list(cmd, True)
            else:
                tcmd = split_cmd_as_list(cmd, False)
            ret = r.execute_command(*tcmd)
            if 'sort_result' in test and isinstance(result[idx], list):
                ret = sort_nested_list(ret)
                result[idx] = sort_nested_list(result[idx])
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
        try:
            run_test(test)
        except Exception as e:
            print(f"run test error {e}", file=logfile)
            continue


def generate_html_report(logdir, configs):
    filepath = f"{logdir}/index.html"
    html = open(filepath, "w")
    html.write("This page is automatically generated by <a href=\"https://github.com/tair-opensource/"
               "compatibility-test-suite-for-redis\">compatibility-test-suite-for-redis</a> "
               "to show the compatibility of the following Redis-Like systems and different versions of Redis.<br><br>")

    # Separate databases into cluster and standalone
    cluster_databases = []
    standalone_databases = []

    for config in configs['Database']:
        if configs['Database'][config]['cluster']:
            cluster_databases.append(config)
        else:
            standalone_databases.append(config)

    # Function to generate a table
    def generate_table(databases, title):
        html.write(f"<h3>{title}</h3>")
        html.write("<table>")
        # generate header
        html.write("<thead>")
        html.write("<tr>")
        html.write("<th>Product / Redis Version</th>")
        for version in configs['SpecificVersion']:
            html.write(f"<th>{version}</th>")
        html.write("</tr>")
        html.write("</thead>")
        # generate body
        html.write("<tbody>")
        for config in databases:
            html.write("<tr>")
            html.write(f"<td>{config}({configs['Database'][config]['version']})</td>")
            for version in configs['SpecificVersion']:
                filepath = f"{logdir}/{config}-{version}.html"
                if not os.path.exists(filepath):
                    html.write(f"<td>-</td>")
                    continue
                with open(filepath, 'r') as f:
                    s = f.read()
                match = re.search(r"rate: (\d+\.\d+)%", s)
                assert match
                rate = match.group(1)
                color = "#40de5a"
                if eval(rate) < 80:
                    color = "#f05654"
                elif eval(rate) < 100:
                    color = "#ffa400"
                html.write(f"<td style=\"background:{color}\">{rate}% <a href=\"{config}-{version}.html\">detail</a></td>")
            html.write("</tr>")
        html.write("</tbody>")
        html.write("</table><br>")

    # Generate standalone table
    generate_table(standalone_databases, "Standalone Databases")

    # Generate cluster table
    generate_table(cluster_databases, "Cluster Databases")

    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html.write(f"This report was generated on {time}.")
    html.write("<style>table {border-collapse: collapse;} th, td {border: 1px solid black; padding: 8px;}</style>")
    html.close()


def start_webserver(logdir):
    os.chdir(logdir)
    handler = http.server.SimpleHTTPRequestHandler
    httpd = http.server.HTTPServer(('', 8000), handler)
    httpd.directory = logdir
    print(f"Visit http://localhost:8000 for the report.")
    httpd.serve_forever()


def run_test_by_configfile():
    global logfile
    try:
        with open('config.yaml', 'r') as f:
            configs = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError as e:
        print(f"error {e}")
        exit(-1)

    logdir = configs['Dir']
    if os.path.exists(logdir):
        print(f"directory {logdir} already exists, will be deleted and renew.")
        shutil.rmtree(logdir)
    os.makedirs(logdir)
    for config in configs['Database']:
        for version in configs['SpecificVersion']:
            print(f"start test {config} for version {version}")
            try:
                create_client(configs['Database'][config]['host'],
                              configs['Database'][config]['port'],
                              configs['Database'][config]['password'],
                              configs['Database'][config]['ssl'],
                              configs['Database'][config]['cluster'])
            except Exception as e:
                print(f"connect to {configs['Database'][config]['host']}:{configs['Database'][config]['port']} "
                      f"fail, skip this test, error {e}")
                break
            filepath = f"{logdir}/{config}-{version}.html"
            logfile = open(filepath, "w")
            args.specific_version = version
            args.show_failed = True
            g_results.clear()
            print("<pre>", file=logfile)
            run_compatibility_tests(args.testfile)
            report_result()
            print("</pre>", file=logfile)
            logfile.close()
            logfile = None
    # now we generate index.html
    generate_html_report(logdir, configs)
    start_webserver(logdir)


def create_client(host, port, password, ssl, cluster):
    global r
    if cluster:
        print(f"connecting to {host}:{port} use cluster client", file=logfile)
        r = redis.RedisCluster(host=host, port=port, password=password, ssl=ssl, decode_responses=True)
        for _, nodes in dict(r.nodes_manager.slots_cache).items():
            for node in nodes:
                node.redis_connection.response_callbacks = {}
        assert r.ping()
    else:
        print(f"connecting to {host}:{port} use standalone client", file=logfile)
        r = redis.Redis(host=host, port=port, password=password, ssl=ssl, decode_responses=True)
        r.response_callbacks = {}
        assert r.ping()


def parse_args():
    parser = argparse.ArgumentParser(prog=" resp_compatibility",
                                     description=" resp_compatibility is used to test whether your redis-like "
                                                 "database is compatible with Redis versions (such as 6.0, 7.0, etc.)",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=EXAMPLE)
    parser.add_argument("--host", help="the redis host", default="127.0.0.1")
    parser.add_argument("--port", help="the redis port", default=6379, type=int)
    parser.add_argument("--password", help="the redis password", default="")
    parser.add_argument("--testfile", help="the redis compatibility test cases", required=True)
    parser.add_argument("--specific-version", dest="specific_version", help="the redis version",
                        choices=['1.0.0', '2.8.0', '3.2.0', '4.0.0', '5.0.0', '6.0.0', '6.2.0', '7.0.0', '7.2.0'])
    parser.add_argument("--show-failed", dest="show_failed", help="show details of failed tests", default=False,
                        action="store_true")
    parser.add_argument("--cluster", help="server is a node of the Redis cluster", default=False, action="store_true")
    parser.add_argument("--ssl", help="open ssl connection", default=False, action="store_true")
    parser.add_argument("--genhtml", help="generate test report in html format", default=False, action="store_true")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.genhtml:
        run_test_by_configfile()
    else:
        create_client(args.host, args.port, args.password, args.ssl, args.cluster)
        run_compatibility_tests(args.testfile)
        report_result()
