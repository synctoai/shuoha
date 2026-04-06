# Distribution

`shuoha` 的用户分发目标很明确：不要求用户先安装 Python、`uv` 或虚拟环境。

当前分发策略：

- 面向普通用户：一行脚本安装预编译二进制
- 面向开发者：保留 `uv` 本地开发路径
- 发布承载：GitHub Releases
- 当前 public binary 默认保证 deterministic 主链路可用，`--agent` 不作为首发分发承诺

## Release Assets

当前约定的 release 产物命名：

- `shuoha-darwin-amd64.tar.gz`
- `shuoha-darwin-arm64.tar.gz`
- `shuoha-windows-amd64.zip`

压缩包内部统一只放一个可执行文件：

- macOS: `shuoha`
- Windows: `shuoha.exe`

## Install Entry Points

macOS:

```bash
curl -fsSL https://raw.githubusercontent.com/synctoai/shuoha/main/scripts/install.sh | sh
```

Windows:

```powershell
irm https://raw.githubusercontent.com/synctoai/shuoha/main/scripts/install.ps1 | iex
```

默认行为：

- 默认安装 `latest` release
- 允许显式安装某个 tag 版本
- 默认写入用户目录，不需要管理员权限

版本示例：

```bash
curl -fsSL https://raw.githubusercontent.com/synctoai/shuoha/main/scripts/install.sh | sh -s -- --version v0.1.0
```

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/synctoai/shuoha/main/scripts/install.ps1))) -Version v0.1.0
```

## Install Locations

macOS:

- binary: `~/.local/bin/shuoha`
- PATH: 通过 shell rc 文件注入 `~/.local/bin`

Windows:

- binary: `%USERPROFILE%\.shuoha\bin\shuoha.exe`
- PATH: 写入用户级 `Path`

## Script Parameters

POSIX 安装脚本支持：

- `--version <tag>`
- `--install-dir <dir>`
- `--repo <owner/name>`

PowerShell 安装脚本支持：

- `-Version <tag>`
- `-InstallDir <dir>`
- `-Repo <owner/name>`

额外环境变量：

- `SHUOHA_REPO`
- `SHUOHA_INSTALL_DIR`

## Upgrade

当前不做自动升级守护。

升级方式很简单：

- 再执行一次安装脚本
- 默认升级到最新 release
- 如果指定 `--version` 或 `-Version`，就安装那个版本

## Uninstall

macOS:

```bash
curl -fsSL https://raw.githubusercontent.com/synctoai/shuoha/main/scripts/uninstall.sh | sh
```

Windows:

```powershell
irm https://raw.githubusercontent.com/synctoai/shuoha/main/scripts/uninstall.ps1 | iex
```

卸载行为：

- 删除二进制文件
- 删除安装脚本写入的 PATH 配置
- 不主动删除项目运行时缓存目录

## Release Workflow

`.github/workflows/release.yml` 负责：

- 监听 `v*` tag
- 构建 `macOS + Windows` 独立二进制
- 打包为约定名称的压缩包
- 上传到 GitHub Release

这份文档只描述 contract，不保证所有平台都已经过手工验收。发布前仍然需要在目标平台做一次真实安装验证。
