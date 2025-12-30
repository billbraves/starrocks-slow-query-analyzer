# Skills vs MCP Server 详细对比与实战示例

## 1. 实际应用场景对比

### 场景 1: SQL 优化分析

#### 📝 Skills 方式（当前项目）

```yaml
# .claude/skills/starrocks_slow_query_analysis.md
---
name: starrocks-slow-query-analysis
description: StarRocks 慢 SQL 分析
parameters:
  time_range: {type: integer, default: 24}
  threshold: {type: number, default: 1.0}
---

# StarRocks 慢 SQL 分析技能

此技能用于分析慢 SQL...

## 使用示例
请帮我分析 StarRocks 过去 24 小时的慢 SQL
```

**特点：**
- ✅ 简单的参数定义
- ✅ 通过提示词引导 AI
- ❌ 需要用户手动运行 Python 脚本
- ❌ AI 无法直接调用数据库
- ❌ 需要依赖外部脚本

#### 🔧 MCP Server 方式

```python
# mcp_server.py
from mcp.server import Server
import pymysql

app = Server("starrocks-mcp-server")

@app.tool()
async def analyze_slow_queries(
    time_range: int = 24,
    threshold: float = 1.0,
    database: str = None
) -> dict:
    """
    分析 StarRocks 慢查询

    Args:
        time_range: 时间范围（小时）
        threshold: 慢查询阈值（秒）
        database: 数据库名称过滤

    Returns:
        慢查询分析结果
    """
    # 直接连接数据库并查询
    conn = pymysql.connect(host="127.0.0.1", port=9030, ...)
    queries = await fetch_slow_queries(conn, time_range, threshold)
    
    # 执行分析
    analysis = analyze_queries(queries)
    
    return {
        "total": len(queries),
        "avg_time": analysis.avg_time,
        "problems": analysis.problems,
        "suggestions": analysis.suggestions
    }

@app.tool()
async def explain_query(sql: str) -> dict:
    """
    获取 SQL 执行计划

    Args:
        sql: SQL 语句

    Returns:
        执行计划详情
    """
    conn = pymysql.connect(...)
    plan = execute_explain(conn, sql)
    return parse_execution_plan(plan)

@app.resource("starrocks://slow-queries")
async def get_slow_queries_resource():
    """
    获取慢查询列表资源
    """
    conn = pymysql.connect(...)
    return fetch_all_slow_queries(conn)

# 启动服务器
if __name__ == "__main__":
    app.run(transport="stdio")
```

**特点：**
- ✅ AI 可以直接调用工具
- ✅ 实时访问数据库
- ✅ 返回结构化数据
- ✅ 可以缓存和优化查询
- ✅ 支持认证和权限控制

### 2. 用户对话体验对比

#### Skills 方式：

```
用户: 请帮我分析 StarRocks 的慢 SQL

AI: 好的，我来帮你分析。根据配置，我需要你运行以下命令：

    python starrocks_slow_query_analyzer.py --time-range 24

    运行完成后，报告将生成在 ./reports/ 目录下。

用户: [手动运行命令]

AI: 看起来报告已生成。让我帮你查看关键发现...

用户: 请帮我分析 orders 表的查询

AI: 请运行以下命令：
    python starrocks_slow_query_analyzer.py --pattern "orders"

用户: [再次手动运行命令]
```

#### MCP Server 方式：

```
用户: 请帮我分析 StarRocks 的慢 SQL

AI: [调用 MCP 工具] analyze_slow_queries(time_range=24)

    分析完成！过去 24 小时发现 156 个慢查询。

    关键发现：
    - 平均执行时间: 3.42s
    - 最慢查询: 45.8s
    - 主要问题: 缺少索引、使用 SELECT *

用户: 请帮我分析 orders 表的查询

AI: [调用 MCP 工具] analyze_slow_queries(pattern="orders")

    找到 42 个与 orders 表相关的慢查询...

用户: 这个 SQL 慢吗？SELECT * FROM orders WHERE status = 'pending'

AI: [调用 MCP 工具] explain_query("SELECT * FROM orders WHERE status = 'pending'")

    让我查看执行计划...

    ⚠️ 这个查询可能较慢：
    - 全表扫描: 扫描 500万 行
    - 建议为 status 列添加索引
    - 避免 SELECT *，只选择需要的列
```

## 3. 核心差异总结

### 数据流对比

```
Skills 方式:
用户 → Claude AI → 生成提示词 → 用户执行 → 返回结果 → AI 分析

MCP Server 方式:
用户 → Claude AI → 调用 MCP 工具 → MCP Server → 数据库/API → 返回数据 → AI 分析
```

### 能力矩阵

| 能力 | Skills | MCP Server |
|------|--------|-------------|
| 参数定义 | ✅ | ✅ |
| 提示词自定义 | ✅ | ✅ |
| 工具调用 | ❌ | ✅ |
| 外部资源访问 | ❌ | ✅ |
| 实时数据查询 | ❌ | ✅ |
| 状态管理 | ❌ | ✅ |
| 异步操作 | ❌ | ✅ |
| 认证授权 | ❌ | ✅ |
| 远程部署 | ❌ | ✅ |
| 缓存优化 | ❌ | ✅ |
| 简单配置 | ✅ | ❌ |
| 零依赖 | ✅ | ❌ |

## 4. 何时使用 Skills

### 适用场景

✅ **使用 Skills 当你需要：**

1. **定制 AI 的行为模式**
   ```yaml
   # .claude/skills/code-review-skill.md
   ---
   name: code-reviewer
   description: 专业代码审查员
   ---
   请以资深架构师的视角审查代码，重点关注：
   - 代码可维护性
   - 性能优化机会
   - 安全隐患
   - 最佳实践遵循
   ```

2. **定义特定领域的知识库**
   ```yaml
   # .claude/skills/kubernetes-expert.md
   ---
   name: k8s-expert
   description: Kubernetes 专家
   ---
   你是 Kubernetes 专家，熟悉：
   - 容器编排
   - 服务发现
   - 负载均衡
   - 自动扩缩容
   ```

3. **标准化的对话流程**
   ```yaml
   # .claude/skills/ci-cd-helper.md
   ---
   name: ci-cd-helper
   description: CI/CD 流程助手
   parameters:
     platform: {type: string, enum: [jenkins, gitlab, github]}
   ---
   请按以下步骤帮助配置 CI/CD：
   1. 理解项目需求
   2. 选择合适的平台
   3. 设计 pipeline
   4. 提供配置文件
   ```

4. **简单的参数化提示**
   ```yaml
   # .claude/skills/code-generator.md
   ---
   name: code-generator
   parameters:
     language: {type: string}
     pattern: {type: string}
   ---
   请生成 {language} 代码，使用 {pattern} 设计模式
   ```

### 优势
- 🚀 快速定义，无需编码
- 📝 声明式，易维护
- 🎯 纯提示词，灵活性高
- 🔒 本地运行，安全可靠

## 5. 何时使用 MCP Server

### 适用场景

✅ **使用 MCP Server 当你需要：**

1. **访问外部数据源**
   ```python
   @app.tool()
   async def query_database(sql: str) -> list:
       """查询数据库"""
       conn = get_database_connection()
       return conn.execute(sql).fetchall()
   ```

2. **执行实际操作**
   ```python
   @app.tool()
   async def create_k8s_deployment(name: str, image: str):
       """创建 Kubernetes 部署"""
       from kubernetes import client, config
       config.load_kube_config()
       # ... 创建部署逻辑
   ```

3. **调用外部 API**
   ```python
   @app.tool()
   async def get_weather(city: str) -> dict:
       """获取天气信息"""
       import requests
       return requests.get(f"api.weather.com/{city}").json()
   ```

4. **文件系统操作**
   ```python
   @app.tool()
   async def analyze_project(path: str) -> dict:
       """分析项目结构"""
       return scan_directory(path)
   ```

5. **复杂业务逻辑**
   ```python
   @app.tool()
   async def optimize_sql(sql: str, database: str) -> dict:
       """SQL 优化 - 包含多步骤分析"""
       # 1. 获取执行计划
       plan = await get_explain_plan(sql)
       # 2. 分析表结构
       schema = await get_table_schema(database)
       # 3. 生成优化建议
       suggestions = generate_optimization(plan, schema)
       return suggestions
   ```

6. **状态管理**
   ```python
   class SessionManager:
       def __init__(self):
           self.sessions = {}

   @app.tool()
   async def create_session(user: str) -> str:
       """创建会话"""
       session_id = generate_id()
       SessionManager.sessions[session_id] = {
           "user": user,
           "created_at": datetime.now()
       }
       return session_id
   ```

### 优势
- 🔧 提供真实可执行的工具
- 🌐 访问任何外部资源
- 💾 支持状态持久化
- 🔐 可实现认证授权
- 🚀 可以优化和缓存
- 📡 支持远程部署

## 6. 实战对比：StarRocks 慢 SQL 分析

### 当前 Skills 方式（已实现）

**优点：**
- ✅ 快速定义分析流程
- ✅ 提供标准化的参数
- ✅ 文档清晰，易于理解

**局限：**
- ❌ AI 无法直接查询数据库
- ❌ 需要用户手动执行脚本
- ❌ 无法实时获取数据
- ❌ 交互体验不够流畅

### 升级为 MCP Server 方式（建议实现）

```python
# mcp_starrocks_server.py
from mcp.server import Server
import pymysql
import asyncio
from typing import Optional

app = Server("starrocks-server")

# 数据库连接池
connection_pool = ConnectionPool(maxsize=10)

@app.tool()
async def analyze_slow_queries(
    time_range: int = 24,
    threshold: float = 1.0,
    database: Optional[str] = None,
    include_details: bool = False
) -> dict:
    """
    分析慢查询
    
    Args:
        time_range: 时间范围（小时）
        threshold: 慢查询阈值（秒）
        database: 数据库名称过滤
        include_details: 是否包含详细信息
    
    Returns:
        分析结果摘要
    """
    async with connection_pool.acquire() as conn:
        # 1. 查询慢 SQL
        queries = await fetch_slow_queries(
            conn, time_range, threshold, database
        )
        
        # 2. 统计分析
        stats = compute_statistics(queries)
        
        # 3. 识别问题
        problems = identify_problems(queries)
        
        # 4. 生成建议
        suggestions = generate_suggestions(problems)
        
        result = {
            "summary": {
                "total_queries": stats.total,
                "avg_execution_time": stats.avg_time,
                "max_execution_time": stats.max_time,
                "severity_distribution": stats.by_severity
            },
            "problems": problems[:10] if not include_details else problems,
            "suggestions": suggestions[:10] if not include_details else suggestions
        }
        
        return result

@app.tool()
async def explain_query(
    sql: str,
    database: Optional[str] = None
) -> dict:
    """
    获取执行计划
    
    Args:
        sql: SQL 语句
        database: 数据库名称
    
    Returns:
        执行计划分析
    """
    async with connection_pool.acquire() as conn:
        # 执行 EXPLAIN
        plan = await execute_explain(conn, sql, database)
        
        # 分析执行计划
        analysis = analyze_execution_plan(plan)
        
        return {
            "sql": sql,
            "execution_plan": plan,
            "analysis": analysis,
            "potential_issues": analysis.issues,
            "optimization_suggestions": analysis.suggestions
        }

@app.tool()
async def get_table_statistics(
    database: str,
    table: str
) -> dict:
    """
    获取表统计信息
    
    Args:
        database: 数据库名
        table: 表名
    
    Returns:
        表统计信息
    """
    async with connection_pool.acquire() as conn:
        stats = await fetch_table_stats(conn, database, table)
        return {
            "row_count": stats.row_count,
            "size": stats.size,
            "indexes": stats.indexes,
            "partitions": stats.partitions
        }

@app.tool()
async def recommend_index(
    sql: str,
    database: str
) -> dict:
    """
    基于查询推荐索引
    
    Args:
        sql: SQL 语句
        database: 数据库名
    
    Returns:
        索引推荐
    """
    # 分析 SQL 的查询模式
    columns = extract_query_columns(sql)
    
    # 获取表结构
    schema = await get_table_schema(database, get_tables(sql))
    
    # 生成推荐
    recommendations = generate_index_recommendations(columns, schema)
    
    return {
        "sql": sql,
        "recommended_indexes": recommendations,
        "expected_improvement": estimate_improvement(recommendations)
    }

@app.resource("starrocks://slow-queries/latest")
async def get_latest_slow_queries():
    """
    获取最新的慢查询
    """
    async with connection_pool.acquire() as conn:
        return await fetch_all_slow_queries(conn, time_range=1)

@app.resource("starrocks://statistics/daily")
async def get_daily_statistics():
    """
    获取每日统计
    """
    async with connection_pool.acquire() as conn:
        return await compute_daily_stats(conn)

# 启动服务器
if __name__ == "__main__":
    app.run(transport="stdio")
```

**优点：**
- ✅ AI 可以直接查询数据库
- ✅ 实时数据，无需用户手动操作
- ✅ 流畅的交互体验
- ✅ 可以连接池优化
- ✅ 支持缓存和历史查询
- ✅ 可以添加认证和审计

## 7. 推荐架构：Skills + MCP Server

### 最佳实践：两者结合使用

```
┌─────────────────────────────────────────┐
│         Claude Code 用户交互             │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌─────────────┐
│ Skills  │    │ MCP Server  │
├─────────┤    ├─────────────┤
│ 定义     │◄──►│ 工具执行     │
│ 参数     │    │ 数据访问     │
│ 提示词   │    │ 业务逻辑     │
│ 工作流   │    │ 状态管理     │
└─────────┘    └─────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  外部资源        │
         │ - 数据库        │
         │ - API           │
         │ - 文件系统      │
         │ - K8s 等        │
         └─────────────────┘
```

### 具体实施方案

**1. Skills - 定义用户界面和交互流程**

```yaml
# .claude/skills/starrocks-assistant.md
---
name: starrocks-assistant
description: StarRocks 性能优化助手
parameters:
  scope:
    type: string
    enum: [monitoring, optimization, troubleshooting]
    default: monitoring
---

你是 StarRocks 性能优化专家，可以帮助：
- 监控慢查询
- 优化 SQL 性能
- 排查性能问题

根据用户需求，调用相应的 MCP 工具：
- analyze_slow_queries: 分析慢查询
- explain_query: 查看执行计划
- recommend_index: 推荐索引
```

**2. MCP Server - 提供实际工具**

```python
# 提供可执行的工具函数
@app.tool()
async def analyze_slow_queries(...) -> dict:
    # 实际的数据库查询和分析逻辑
    pass
```

### 结合使用的优势

1. **Skills 负责什么**
   - 📝 定义交互模式
   - 🎯 引导用户提问
   - 📚 提供领域知识
   - 🔄 标准化响应格式

2. **MCP Server 负责什么**
   - 🔧 执行实际操作
   - 🌐 访问外部资源
   - 💾 管理状态和缓存
   - 🔐 处理认证授权

3. **协同效果**
   - ✅ 最好的用户体验
   - ✅ 最强的功能能力
   - ✅ 最灵活的架构
   - ✅ 最易维护的代码

## 8. 迁移建议

### 当前项目（Skills）→ 升级路径

**阶段 1: 保留 Skills（已完成）**
- ✅ 定义清晰的交互流程
- ✅ 提供参数配置
- ✅ 用户可以手动运行脚本

**阶段 2: 开发 MCP Server（建议实施）**
1. 创建 `mcp_server.py`
2. 实现核心工具函数
3. 添加数据库连接池
4. 实现缓存机制
5. 添加认证（如需要）

**阶段 3: 深度集成**
1. 更新 Skill 文档，说明 MCP 工具的使用
2. AI 自动识别并调用 MCP 工具
3. 提供无缝的交互体验

**阶段 4: 高级功能**
1. 添加实时监控
2. 实现告警机制
3. 集成到 CI/CD
4. 添加权限管理

## 9. 总结

| 方面 | Skills | MCP Server | 推荐 |
|------|--------|-------------|------|
| 定义简单任务 | ✅ 优秀 | ⚠️ 过度设计 | Skills |
| 定制 AI 行为 | ✅ 优秀 | ❌ 不适用 | Skills |
| 访问数据库 | ❌ 不支持 | ✅ 优秀 | MCP Server |
| 执行操作 | ❌ 不支持 | ✅ 优秀 | MCP Server |
| 状态管理 | ❌ 有限 | ✅ 优秀 | MCP Server |
| 快速原型 | ✅ 优秀 | ⚠️ 需要编码 | Skills |
| 生产环境 | ⚠️ 有限 | ✅ 优秀 | MCP Server |
| **最终建议** | | | **两者结合** |

### 核心建议

1. **先用 Skills** - 快速验证想法和用户需求
2. **后加 MCP** - 当需要真实数据访问和操作时升级
3. **持续集成** - 两者配合使用，发挥各自优势

---

**下一步建议：**

基于你的 StarRocks 慢 SQL 分析项目，建议：

1. ✅ 保留当前的 Skills 定义（已完成）
2. 🚀 开发 MCP Server 版本
3. 🔗 两者深度集成
4. 📊 提供完整的解决方案

这样既能享受 Skills 的简单性，又能获得 MCP Server 的强大能力！

