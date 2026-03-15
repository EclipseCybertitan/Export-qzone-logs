# qzone-text-exporter

把 QQ 空间日志导出成可审计、可检索、可离线处理的纯文本资产，并提供后处理管线（合并、去重、质量分级、索引生成）。

一句话定位：这是把“日志”变成“本地隐私 AI 日记/日志（RAG/知识库）可用输入”的前置条件工具。

作者签名：月蚀之夜
作者联系邮箱：tasks-09swapper@icloud.com

English README: see `README.en.md`.

## 主要特性

- 只做“日志 -> 纯文本文件”，不做全站备份框架（相册/留言/说说等不在范围内）。
- cookie 只从本地 `--cookie-file` 读取，不出现在命令行参数中，降低泄露风险。
- 端点 fallback + JSONP 松散解析，更耐站点变化。
- HTML 正文提取避免嵌套 `div` 正则截断（使用“起始锚点 + 终止锚点”或 HTMLParser 策略）。
- 后处理：多目录合并、按 `blog_id` 去重、正文长度分级、幂等重命名前缀、生成质量索引。

## 安装

```bash
python -m pip install .
```

或用 `pipx`：

```bash
pipx install .
```

## 使用

### 1) 准备 cookie 文件（不要提交/不要发到 issue）

创建本地文件 `cookie.txt`（只在你机器上存在），内容是一行标准 Cookie header，例如：

```text
p_skey=...; skey=...; uin=o<UIN>; p_uin=o<UIN>; pt4_token=...;
```

必须包含 `skey` 或 `p_skey`，用于计算 `g_tk`。

### 2) 导出日志为纯文本

```bash
qzone-text-exporter export \
  --uin <UIN> \
  --cookie-file /path/to/cookie.txt \
  --out-dir /path/to/exports
```

输出：

- `qzone_logs_all.csv`：含 `title,published_date,blog_id`
- 每篇一文件：`<title> - <YYYY-MM-DD>.txt`
- `index.csv`：写入状态与错误信息（便于补跑/定位失败）

可选：

- `--resume`：跳过已导出且校验通过的文章
- `--rate-limit-ms 500`：请求节流
- `--retry 3`：失败重试次数
- `--max-posts 10`：调试/抽样

### 3) 后处理（合并、去重、分级、重命名）

```bash
qzone-text-exporter postprocess \
  --out-dir /path/to/merged \
  --merge-dirs /path/to/exports1,/path/to/exports2 \
  --dedupe \
  --quality-buckets \
  --rename-prefix
```

生成：

- `index_quality.csv`：`class,body_len,filename,blog_id`

## 经验坑位（开源价值点）

- **端点/路由**：日志列表常见用 `get_abs`，正文用 `blog_output_data`；不同域名/代理链可能返回 403/404，需要 fallback。
- **JSONP 解析**：不要用过严正则，推荐“首个 `(` 到最后一个 `)`”提取 JSON。
- **正文提取**：不要用 `.*?</div>` 截嵌套 `div`，会提前截断导致“空文”。推荐锚点截段或 HTMLParser。
- **安全工作流**：cookie 只进本地文件；仓库 `.gitignore` 强制屏蔽；issue/PR 不要贴 cookie。
- **后处理定位**：导出只是第一步；后处理让内容更适合作为本地隐私 AI 日记/日志的输入资产。

## 生态与竞品（为什么还值得做）

同类项目/库已经存在，例如：

- [ShunCai/QZoneExport](https://github.com/ShunCai/QZoneExport)：浏览器扩展，覆盖范围更偏“全量备份”（多类型内容与附件）。
- [aioqzone](https://pypi.org/project/aioqzone/) 等 Python 库：更偏 API 封装/自动化能力，本项目关注点不同。

本项目的角度仍有价值：

- 目标更窄更明确：只把“日志”稳定变成“纯文本资产”，并把后处理当作一等公民。
- 输出面向“本地隐私 AI 日记/日志（RAG/知识库）”：合并、去重、质量分级、索引生成都是默认链路的一部分。
- 工程化坑位明确可测试：JSONP 松散解析、端点 fallback、HTML 正文提取避免嵌套 `div` 截断（空文）等都有单测覆盖。

## 免责声明

仅供你在你有权限的数据范围内使用。请遵守当地法律法规与目标站点条款。详见 `SECURITY.md`。
