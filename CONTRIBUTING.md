# Contributing

`shuoha` 现在还是一个很早期的 CLI 项目。  
如果你要参与开发，先记住一个原则：

> 这个项目是 evidence-first，不是 prompt-first。

也就是说：

- 先有结构化数据和确定性规则
- 再有给人看的中文解释
- LLM 可以润色表达，但不应该替代底层判决

## 开发环境

环境要求：

- Python `3.12+`
- `uv`

安装依赖：

```bash
uv sync --extra dev
```

如果你要调试 `--agent`：

```bash
uv sync --extra dev --extra agent
export OPENAI_API_KEY=你的密钥
```

## 开发前先理解的目录

```text
src/shuoha/
  cli.py                         # 命令入口
  engine.py                      # 分析主流程
  indicators.py                  # 技术指标
  rules.py                       # 确定性结论规则
  schemas.py                     # AnalysisResult / EvidenceItem 等 schema
  data/providers/
    base.py                      # ProviderPayload 抽象
    akshare_provider.py          # 当前 A 股 provider
  reporting/
    markdown_renderer.py         # report.md
    terminal_renderer.py         # 终端输出
    agent_renderer.py            # 可选 LLM 改写层
    output.py                    # 落盘
tests/
```

建议的理解顺序：

1. 看 [src/shuoha/schemas.py](/Users/leeeeeee/code/shuoha/src/shuoha/schemas.py)
2. 看 [src/shuoha/engine.py](/Users/leeeeeee/code/shuoha/src/shuoha/engine.py)
3. 看 [src/shuoha/rules.py](/Users/leeeeeee/code/shuoha/src/shuoha/rules.py)
4. 再看 provider 和 renderer

## 基本开发命令

运行全部测试：

```bash
uv run --extra dev pytest -v
```

跑一个真实样例：

```bash
uv run shuoha analyze 600519
uv run shuoha analyze 600519 --full
```

查看 CLI 参数：

```bash
uv run shuoha analyze --help
```

## 提交改动时的基本要求

任何改动都尽量满足下面这几点：

- 不要让 LLM 直接生成 verdict
- 不要绕过 `AnalysisResult` / `EvidenceItem` 这些 schema
- 不要只改解释文案而不考虑 `evidence.json` 是否仍然合理
- 不要把 README 写得比真实实现更强
- 用户可见行为变化，必须补测试或至少补验证路径

## 如何新增一个 Provider

目标不是“再接一个接口”，而是“接一个能稳定产出 `ProviderPayload` 的数据源”。

当前 provider contract 在 [base.py](/Users/leeeeeee/code/shuoha/src/shuoha/data/providers/base.py)：

- 必须返回 `ProviderPayload`
- 至少包含：
  - `stock_code`
  - `company_name`
  - `industry`
  - `company_summary`
  - `daily_history`
  - `as_of_date`

新增 provider 时建议遵守：

1. 先在 `data/providers/` 下实现一个独立 provider 文件
2. 先把第三方数据归一化成当前系统使用的字段，不要把外部字段名传进 engine
3. provider 层自己处理 fallback、缓存、异常降级
4. `engine.py` 只消费统一后的 payload，不要掺杂 provider 特例

建议补的测试：

- 历史行情排序和字段归一化
- provider 失败后的 fallback
- 空资料或脏数据时的降级行为
- 缓存命中行为

可以参考 [test_akshare_provider.py](/Users/leeeeeee/code/shuoha/tests/test_akshare_provider.py)。

## 如何新增一个指标

新增指标时，分清两层：

- 指标计算本身
- 指标如何转成证据

建议流程：

1. 先在 [indicators.py](/Users/leeeeeee/code/shuoha/src/shuoha/indicators.py) 增加纯计算函数
2. 在 [engine.py](/Users/leeeeeee/code/shuoha/src/shuoha/engine.py) 里把指标结果转成 `EvidenceItem`
3. 明确它是：
   - `positive`
   - `neutral`
   - `negative`
4. 再让 renderer 去解释这条证据

不要做的事：

- 在 renderer 里偷偷补逻辑
- 直接把一段自由文本当作新“指标”
- 在规则层引用一个没有稳定 schema 的原始字符串

建议补的测试：

- 指标函数自己的边界测试
- `engine` 里新增证据是否被正确产出

## 如何调整 verdict 规则

结论规则在 [rules.py](/Users/leeeeeee/code/shuoha/src/shuoha/rules.py)。

这里是项目的高风险区域，因为它会直接影响：

- `verdict`
- `confidence`
- `bias`
- 用户对整个工具的信任

改规则时建议遵守：

1. 先明确你在改什么
   - 提高保守性
   - 放宽关注条件
   - 调整 bias 门槛
2. 先补规则测试，再改实现
3. 至少覆盖：
   - 明显偏多
   - 明显偏空
   - 混合信号
   - partial / 降级场景

可以参考：

- [test_rules.py](/Users/leeeeeee/code/shuoha/tests/test_rules.py)
- [test_engine.py](/Users/leeeeeee/code/shuoha/tests/test_engine.py)

## 如何改报告层

当前有 3 层输出：

- `terminal_renderer.py`
  - 给 CLI 直接看
- `markdown_renderer.py`
  - 给 `report.md`
- `agent_renderer.py`
  - 给 `--agent` 路径做文风重写

修改报告层时要守住边界：

- 终端可读性问题，优先改 `terminal_renderer.py`
- Markdown 结构问题，改 `markdown_renderer.py`
- LLM 改写问题，改 `agent_renderer.py`
- 不要把业务判决逻辑塞进 renderer

如果是文案增强，至少确认：

- 新手能看懂
- 没有暗示“自动下单”
- 没有说出证据里不存在的事实

## 测试策略

当前测试分层大致是：

- `test_indicators.py`
  - 纯计算函数
- `test_rules.py`
  - verdict 规则
- `test_engine.py`
  - 分析主流程和 partial 降级
- `test_akshare_provider.py`
  - provider 归一化、fallback、缓存、并发
- `test_markdown_renderer.py`
  - Markdown 报告结构
- `test_terminal_renderer.py`
  - 终端可读性
- `test_cli.py`
  - CLI 参数和输出模式

如果你新增功能，尽量把测试落在最靠近变更的层，而不是一股脑全堆到 CLI。

## 提交建议

建议 commit message 直接描述结果，而不是描述过程：

- `feat: add xxx`
- `fix: handle xxx gracefully`
- `docs: explain xxx`

避免：

- `update`
- `misc changes`
- `fix stuff`

## 目前最值得做的方向

如果你想贡献高价值改动，优先考虑这些方向：

- 股票名称搜索和代码补全
- 更稳定的 provider/fallback contract
- 更完整的基本面和估值信息
- thesis/watch 持久化跟踪
- 多角色输出
- 更强的回放测试和 fixture 数据

## 最后一个原则

这个项目可以写得更复杂，但不应该更糊涂。  
每次改动都应该让下面三件事至少有一件变好：

- 证据更稳
- 结论更清楚
- 新手更看得懂
