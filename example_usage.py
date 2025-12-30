#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StarRocks 慢 SQL 分析工具 - 使用示例
演示各种使用场景和 API
"""

from starrocks_slow_query_analyzer import StarRocksSlowQueryAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_analysis():
    """示例 1: 基础慢 SQL 分析"""
    print("=" * 60)
    print("示例 1: 基础慢 SQL 分析")
    print("=" * 60)
    
    # 创建分析器
    analyzer = StarRocksSlowQueryAnalyzer('config.yaml')
    
    # 执行分析 - 分析过去 24 小时的慢查询
    report_path = analyzer.analyze(
        time_range_hours=24,
        min_execution_time=1.0
    )
    
    print(f"\n✅ 分析完成！报告路径: {report_path}\n")


def example_filtered_analysis():
    """示例 2: 过滤条件分析"""
    print("=" * 60)
    print("示例 2: 过滤条件分析")
    print("=" * 60)
    
    analyzer = StarRocksSlowQueryAnalyzer('config.yaml')
    
    # 只分析特定数据库的慢查询
    report_path = analyzer.analyze(
        time_range_hours=6,
        min_execution_time=0.5,
        database_filter='your_database'  # 替换为你的数据库名
    )
    
    print(f"\n✅ 分析完成！报告路径: {report_path}\n")


def example_pattern_filter():
    """示例 3: SQL 模式过滤"""
    print("=" * 60)
    print("示例 3: SQL 模式过滤")
    print("=" * 60)
    
    analyzer = StarRocksSlowQueryAnalyzer('config.yaml')
    
    # 只分析与特定表相关的查询
    report_path = analyzer.analyze(
        time_range_hours=12,
        min_execution_time=1.0,
        pattern_filter='orders'  # 只分析包含 "orders" 的 SQL
    )
    
    print(f"\n✅ 分析完成！报告路径: {report_path}\n")


def example_get_top_slow_queries():
    """示例 4: 获取最慢的查询"""
    print("=" * 60)
    print("示例 4: 获取最慢的查询")
    print("=" * 60)
    
    analyzer = StarRocksSlowQueryAnalyzer('config.yaml')
    
    # 获取过去 24 小时最慢的 10 个查询
    top_queries = analyzer.get_top_slow_queries(limit=10, time_range_hours=24)
    
    print(f"\n📊 最慢的 {len(top_queries)} 个查询:\n")
    for i, query in enumerate(top_queries, 1):
        print(f"{i}. Query ID: {query.query_id}")
        print(f"   数据库: {query.database}")
        print(f"   执行时间: {query.execution_time:.2f}s")
        print(f"   扫描行数: {query.scan_rows_formatted}")
        print(f"   严重程度: {query.severity}")
        print(f"   SQL: {query.query_text[:100]}...")
        print()


def example_analyze_specific_sql():
    """示例 5: 分析特定的 SQL 语句"""
    print("=" * 60)
    print("示例 5: 分析特定的 SQL 语句")
    print("=" * 60)
    
    analyzer = StarRocksSlowQueryAnalyzer('config.yaml')
    
    # 要分析的 SQL
    sql = """
    SELECT * FROM orders 
    WHERE create_time > '2024-01-01' 
    AND status IN ('pending', 'processing')
    ORDER BY create_time DESC
    LIMIT 1000
    """
    
    # 分析 SQL
    result = analyzer.analyze_specific_sql(sql)
    
    print(f"\n📝 分析 SQL:\n{sql}\n")
    
    if result['problems']:
        print("⚠️  发现的问题:")
        for problem in result['problems']:
            print(f"\n  类型: {problem['type']} [{problem['severity']}]")
            print(f"  描述: {problem['description']}")
            print(f"  建议: {problem['suggestion']}")
    else:
        print("✅ 未发现明显问题")
    
    if result['suggestions']:
        print("\n💡 优化建议:")
        for suggestion in result['suggestions']:
            print(f"\n  {suggestion['title']} [{suggestion['priority']}]")
            print(f"  {suggestion['description']}")
            if suggestion['suggested_sql']:
                print(f"\n  优化 SQL:\n  {suggestion['suggested_sql']}")
            if suggestion['estimated_improvement']:
                print(f"  预期提升: {suggestion['estimated_improvement']}")
    print()


def example_custom_config():
    """示例 6: 自定义配置分析"""
    print("=" * 60)
    print("示例 6: 自定义配置分析")
    print("=" * 60)
    
    # 创建自定义配置的分析器
    analyzer = StarRocksSlowQueryAnalyzer('config.yaml')
    
    # 修改报告格式
    analyzer.report_generator.report_format = 'markdown'
    
    # 修改阈值
    report_path = analyzer.analyze(
        time_range_hours=48,
        min_execution_time=2.0
    )
    
    print(f"\n✅ 分析完成！Markdown 报告路径: {report_path}\n")


def example_multiple_reports():
    """示例 7: 生成多个格式的报告"""
    print("=" * 60)
    print("示例 7: 生成多个格式的报告")
    print("=" * 60)
    
    analyzer = StarRocksSlowQueryAnalyzer('config.yaml')
    
    formats = ['html', 'markdown', 'json']
    report_paths = []
    
    for fmt in formats:
        # 修改报告格式
        analyzer.report_generator.report_format = fmt
        
        # 执行分析
        report_path = analyzer.analyze(
            time_range_hours=6,
            min_execution_time=1.0
        )
        
        report_paths.append((fmt, report_path))
        print(f"✅ {fmt.upper()} 报告已生成: {report_path}")
    
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("StarRocks 慢 SQL 分析工具 - 使用示例")
    print("=" * 60 + "\n")
    
    examples = [
        ("基础慢 SQL 分析", example_basic_analysis),
        ("过滤条件分析", example_filtered_analysis),
        ("SQL 模式过滤", example_pattern_filter),
        ("获取最慢的查询", example_get_top_slow_queries),
        ("分析特定的 SQL", example_analyze_specific_sql),
        ("自定义配置分析", example_custom_config),
        ("生成多个格式报告", example_multiple_reports),
    ]
    
    print("可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print(f"\n  0. 运行所有示例")
    print(f"  q. 退出\n")
    
    while True:
        try:
            choice = input("请选择要运行的示例 (0-7/q): ").strip()
            
            if choice.lower() == 'q':
                print("\n👋 再见！")
                break
            
            choice = int(choice)
            
            if choice == 0:
                # 运行所有示例
                for name, func in examples:
                    try:
                        func()
                        input("\n按 Enter 继续...")
                    except Exception as e:
                        print(f"\n❌ 示例执行失败: {str(e)}")
                        input("\n按 Enter 继续...")
            elif 1 <= choice <= len(examples):
                # 运行选定示例
                name, func = examples[choice - 1]
                try:
                    func()
                except Exception as e:
                    print(f"\n❌ 示例执行失败: {str(e)}")
                    print("\n💡 提示: 请确保配置文件 config.yaml 中的数据库连接信息正确")
                    print("💡 提示: 确认 StarRocks 的 query_log 功能已开启")
            else:
                print("\n❌ 无效的选择，请重新输入")
        
        except ValueError:
            print("\n❌ 请输入有效的数字")
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break


if __name__ == '__main__':
    main()

