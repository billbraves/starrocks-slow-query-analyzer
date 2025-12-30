# StarRocks 慢 SQL 分析系统

## 🎯 项目简介

这是一个专为 StarRocks 数据库设计的慢 SQL 分析和优化工具，集成到 Claude Code 的自定义 Skills 中，可以自动识别、诊断和优化慢查询，提供性能优化建议。

## ✨ 核心功能

- **慢 SQL 自动收集** - 从 StarRocks 的查询日志中自动收集慢查询
- **智能分析诊断** - 分析 SQL 结构、执行计划，识别性能瓶颈
- **优化建议生成** - 提供针对性的优化建议和 SQL 改写方案
- **多格式报告** - 支持 HTML、Markdown、JSON 三种报告格式
- **Claude Code 集成** - 通过自定义 Skills 深度集成到 Claude Code

## 📋 系统要求

- Python 3.8+
- StarRocks 2.0+
- Claude Code（使用自定义 Skills 功能）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库连接

编辑 `config.yaml` 文件：

```yaml
database:
  host: "127.0.0.1"
  port: 9030
  user: "root"
  password: ""
  database: "information_schema"

slow_query_threshold: 1.0  # 慢查询阈值（秒）
analysis_time_range: 24     # 分析时间范围（小时）
```

### 3. 运行分析

#### 命令行方式

```bash
# 分析过去 24 小时的慢查询
python starrocks_slow_query_analyzer.py

# 自定义时间范围和阈值
python starrocks_slow_query_analyzer.py --time-range 6 --threshold 0.5

# 指定数据库和报告格式
python starrocks_slow_query_analyzer.py --database my_db --format html
```

#### Python API 方式

```python
from starrocks_slow_query_analyzer import StarRocksSlowQueryAnalyzer

# 创建分析器
analyzer = StarRocksSlowQueryAnalyzer('config.yaml')

# 执行分析
report_path = analyzer.analyze(
    time_range_hours=24,
    min_execution_time=1.0,
    database_filter='your_database'
)

print(f"报告已生成: {report_path}")
```

#### 在 Claude Code 中使用

配置自定义 Skills 后，在 Claude Code 中直接对话：

```
请帮我分析 StarRocks 过去 24 小时的慢 SQL

请详细分析与表 orders、users 相关的慢查询

请诊断这个 SQL 的性能问题：
SELECT * FROM orders WHERE create_time > '2024-01-01'
```

## 📊 报告示例

分析完成后会生成详细的报告，包括：

### 统计概览
- 总慢查询数
- 平均/最大执行时间
- 总扫描行数
- 严重程度分布

### 慢查询详情
- Query ID 和 SQL 文本
- 性能指标（执行时间、扫描行数、内存使用等）
- 发现的问题列表
- 优化建议

### 优化建议汇总
- 按优先级排序的建议列表
- 预期性能提升
- 实施说明

## 🏗️ 项目结构

```
.
├── starrocks_connector.py          # 数据库连接器
├── slow_query_collector.py         # 慢 SQL 收集器
├── query_analyzer.py               # SQL 分析器
├── optimization_suggester.py       # 优化建议生成器
├── report_generator.py             # 报告生成器
├── starrocks_slow_query_analyzer.py # 主程序
├── config.yaml                     # 配置文件
├── requirements.txt                # 依赖列表
├── .claude/
│   └── skills/
│       └── starrocks_slow_query_analysis.md  # Claude Code Skill 配置
└── README.md
```

## 🔧 配置说明

### config.yaml 配置项

```yaml
# 数据库连接配置
database:
  host: "127.0.0.1"        # StarRocks FE 地址
  port: 9030               # FE 端口
  user: "root"             # 用户名
  password: ""             # 密码
  database: "information_schema"  # 数据库

# 慢查询阈值配置
slow_query_threshold: 1.0         # 慢查询最小执行时间（秒）
very_slow_query_threshold: 5.0    # 严重慢查询阈值
critical_query_threshold: 10.0    # 严重慢查询阈值

# 分析时间范围
analysis_time_range: 24            # 分析时间范围（小时）

# 输出配置
output:
  report_dir: "./reports"          # 报告输出目录
  report_format: "html"            # 报告格式
  include_query_plans: true        # 是否包含执行计划

# 优化建议配置
optimization:
  max_scan_rows: 10000000          # 最大扫描行数阈值
  max_scan_bytes: 1073741824       # 最大扫描字节数（1GB）
  suggest_indexes: true            # 是否建议创建索引
```

## 💡 使用技巧

### 1. 定期巡检

```bash
# 每天凌晨 2 点执行分析
0 2 * * * /path/to/python starrocks_slow_query_analyzer.py --time-range 24
```

### 2. 针对性分析

```bash
# 分析特定数据库
python starrocks_slow_query_analyzer.py --database analytics_db

# 分析包含特定表名的查询
python starrocks_slow_query_analyzer.py --pattern "orders"

# 分析特定用户的查询
python starrocks_slow_query_analyzer.py --user "data_team"
```

### 3. 在 Claude Code 中智能交互

```
# 综合分析
请帮我分析过去 6 小时的慢 SQL，重点关注执行时间超过 5 秒的查询

# 深度诊断
请详细分析以下 SQL 并提供优化方案：
[粘贴你的 SQL]

# 持续监控
请帮我把慢 SQL 分析加入到日常巡检流程中
```

## 📈 优化建议类型

系统会识别并提供以下类型的优化建议：

### 索引优化
- 识别缺少索引的查询
- 建议创建合适的索引
- 优化索引使用策略

### SQL 结构优化
- 避免 SELECT *
- 优化 OR 条件
- 改进 LIKE 查询
- 优化子查询

### 查询性能优化
- 减少扫描行数
- 利用分区裁剪
- 优化 JOIN 操作
- 优化聚合查询

### 配置优化
- 内存使用建议
- 执行引擎参数调整

## 🐛 常见问题

### 1. 无法连接到 StarRocks

- 检查 `config.yaml` 中的连接配置
- 确认 FE 服务是否正常运行
- 检查网络连通性

### 2. 没有慢查询数据

- 确认 `query_log` 功能是否开启
- 检查时间范围设置是否合理
- 确认阈值设置是否过低

### 3. 分析报告不完整

- 检查日志文件获取详细错误信息
- 确认有足够的磁盘空间
- 检查权限设置

## 📚 技术架构

```
┌─────────────────────────────────────┐
│   Claude Code (自定义 Skills)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   StarRocksSlowQueryAnalyzer        │
├─────────────────────────────────────┤
│  ├── StarRocksConnector             │  数据库连接
│  ├── SlowQueryCollector             │  慢查询收集
│  ├── QueryAnalyzer                  │  SQL 分析
│  ├── OptimizationSuggester          │  优化建议
│  └── ReportGenerator                │  报告生成
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   StarRocks (information_schema)     │
└─────────────────────────────────────┘
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👥 作者

大数据研发工程师 - 专为 StarRocks 性能优化设计

## 🙏 致谢

感谢 StarRocks 社区和 Claude Code 团队提供的优秀工具。

