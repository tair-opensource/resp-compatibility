# compatibility-test-suite-for-redis

`compatibility-test-suite-for-redis`是一个用来检测你的`Redis-Like`系统兼容到开源`Redis`哪个版本的工具（6.0还是7.0等）。

# 安装

要求`Python 3.7`及以上版本。
```
pip3 install -r requirements.txt
```

# 可测试命令

CTS 可以测试的命令及其对应的版本信息可参考[此表](cts_refer.md)

# 如何使用

一些命令行支持的参数如下所示：

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
例如，测试 host:port 对应的服务是否兼容 Redis 6.2.0 版本并显示失败的测试。
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
更多的示例请参考 `python3 redis_compatibility_test.py -h`。

## cluster
Redis 在 API 层面有两种模式，一个是`Standalone`（Sentinel 模式的 API 兼容性和 Standalone 是一样的），一个是`Cluster`。命令在`Standalone`模式下没有跨 Slot 的限制，但是在集群模式下，要求多 key 的命令（例如 mset/mget命令）必须在同一 Slot 中。因此，我们支持了`--cluster`这个选项来测试系统对于 `Redis Cluster` 模式的兼容性，用法如下：
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
您可以使用 `--genhtml` 选项来生成和此[网站](https://tair-opensource.github.io/compatibility-test-suite-for-redis/)相同的 html 报告。 请注意，当使用此选项时候，将会读取 [config.yaml](config.yaml) 文件中的配置进行测试，此时命令行中的 `specific-version` 将会被文件中的覆盖。
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
结束之后，一个 HTTP 服务器将会被启动在 http://localhost:8000 ，您可以访问此网站获得 html 报告。

## 更多用法

### 在迁移您的业务之前验证数据库的支持
当您需要将业务系统从 A 数据库迁移到 B 时，为了防止 B 的不兼容，您可以编写自己的 `cts.json` (compatibility-test-suite) 来验证 B 数据库系统兼容性，其格式示例如下：
```
[
  {
    "name": "del command",
    "command": [
      "set k v",
      "del k"
    ],
    "result": [
      "OK",
      1
    ],
    "since": "1.0.0"
  }
]
```
整体上是一个 JSON数组，包含多条测试 case，每一个都是 JSON Object，`command`和`result`是一一对应的。除过上述示例中的字段，还有一些字段如下：

| name           | value              | 含义                          |
|----------------|--------------------|-----------------------------|
| tags           | standalone,cluster | 只在tags指定的模式下才允许此case        |
| skipped        | true               | 跳过此case                     |
| command_binary | true               | 将命令转为二进制，例如命令中包含非可见的ascii字符 |
| sort_result    | true               | 对返回结果进行排序                   |

### 使用别的编程语言使用此工具
本项目的主要工作是我们在 `cts.json`中增加了超过 7000 行测试，如果您希望用别的编程语言（例如 Java, Go, Rust等）实现相同功能的测试工具，那么您只需要解析 `cts.json` 的格式，并且将测试依次执行即可，玩的愉快。
## License
[MIT](LICENSE)