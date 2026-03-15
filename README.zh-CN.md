# qzone-text-exporter（中文）

把 QQ 空间日志导出成可审计、可检索、可离线处理的纯文本资产，并提供后处理管线（合并、去重、质量分级、索引生成）。

一句话定位：这是把“日志”变成“本地隐私 AI 日记/日志（RAG/知识库）可用输入”的前置条件工具。

签名：月蚀之夜

作者联系邮箱：tasks-09swapper@icloud.com

## 安全提示（非常重要）

- cookie 只放在本地文件里，通过 `--cookie-file` 读取。
- 不要把 cookie 粘贴到 issue/PR/截图/日志里。
- 不要把导出结果（你的日记/日志）提交到 git。

## 快速开始

1) 安装：

```bash
python -m pip install .
```

2) 准备 cookie 文件（只在本机）：

参考 `cookie.example.txt`，创建你自己的 `cookie.txt`。

3) 导出：

```bash
qzone-text-exporter export --uin <UIN> --cookie-file /path/to/cookie.txt --out-dir /path/to/exports
```

4) 后处理（合并/去重/分级/重命名）：

```bash
qzone-text-exporter postprocess \
  --out-dir /path/to/merged \
  --merge-dirs /path/to/exports1,/path/to/exports2 \
  --dedupe --quality-buckets --rename-prefix
```

## 文档

- 项目核心 README：`README.md`
- 安全与隐私：`SECURITY.md`
