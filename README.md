# QFGraph

二次函数绘图工具，使用 Qt Widgets 和 QCustomPlot。

## 本地构建 macOS Universal

需要 macOS、Xcode Command Line Tools、Python 3.9+，以及同时包含
`arm64` 和 `x86_64` 的 Qt。当前已验证 Qt 6.8.3 官方 macOS 库。
仅包含 arm64 的 Homebrew Qt 不能用于生成完整的 Universal 包。

```sh
make configure QT_ROOT=/path/to/Qt/6.8.3/macos
make
```

`QT_ROOT` 指向包含 `bin/qmake`、`lib` 和 `plugins` 的目录，具体目录名以实际安装为准。
首次配置会将路径和 Qt 工具运行架构保存到 git 忽略的 `config.mk`；之后直接运行 `make`。
未配置时才会尝试使用 PATH 中的 qmake。如果它指向仅有 arm64 的 Homebrew Qt，
默认 Universal 构建会报架构不匹配，需要先选择双架构 Qt，不能仅靠运行 `make` 补齐依赖。
需要 Rosetta 时，配置命令中加上 `QT_HOST_ARCH=x86_64`。
构建会生成主程序、收集 Qt 运行依赖、检查所有二进制架构及依赖完整性、
添加本地临时签名，并生成：

- `dist/QFGraph-Universal.app`
- `dist/QFGraph-macOS-Universal.zip`

应用未进行 Apple Developer 签名或公证。

```sh
# 仅构建一种架构
make QT_ROOT=/path/to/Qt ARCHS=arm64
make QT_ROOT=/path/to/Qt ARCHS=x86_64

# 在 Apple Silicon 上用 Rosetta 运行 Qt 的构建工具（需要安装 Rosetta）
make QT_ROOT=/path/to/Qt QT_HOST_ARCH=x86_64

# 单独检查已有应用包
make verify

# 在图形登录会话中逐一测试请求的架构，每种启动 8 秒
make smoke

# 清理当前架构的编译目录；保留 dist 中的成品
make clean
```

可设置 `JOBS`（默认 4）、`MACOS_MIN`（默认 12.0）、`BUILD_DIR`、`DIST_DIR`。
切换 Qt 安装或构建参数时，先执行 `make clean`，或指定新的 `BUILD_DIR`。
使用单架构成品时，验证和启动命令也需传相同的 `ARCHS`、`DIST_DIR`。

受限的运行环境可能禁止 Qt 6.8 读取 Apple Silicon 的 CPU 特性，
或阻止访问窗口服务；此时 `make smoke` 会报告失败，不代表启动验证已通过。

## Windows

Windows x64 构建通过 `.github/workflows/windows-release.yml` 使用 MSVC 和 Qt，
在 GitHub Actions 中编译、打包并验证启动。
