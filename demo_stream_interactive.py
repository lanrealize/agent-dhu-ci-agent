#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""流式对话演示 - Windows 终端优化版"""

import requests
import json
import time
import sys

def clear_line():
    """清除当前行"""
    sys.stdout.write('\r' + ' ' * 80 + '\r')
    sys.stdout.flush()

def print_with_timestamp(msg, prefix="", flush=True):
    """带时间戳的打印"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {prefix}{msg}", flush=flush)

def animate_thinking():
    """显示思考动画"""
    for i in range(3):
        sys.stdout.write(f"\r[思考中{'.' * (i + 1)}{'  ' * (2 - i)}]")
        sys.stdout.flush()
        time.sleep(0.3)
    sys.stdout.write('\r' + ' ' * 40 + '\r')
    sys.stdout.flush()

def test_single_query():
    """测试单个查询"""
    url = "http://127.0.0.1:8006/api/v1/chat/stream"

    print("\n" + "="*80)
    print("流式对话演示 - 实时显示")
    print("="*80)
    print("\n问题: 请查询 my-project 的测试覆盖率\n")

    data = {
        "message": "请查询 my-project 的测试覆盖率",
        "session_id": None
    }

    start_time = time.time()
    tool_count = 0
    session_id = None

    try:
        print_with_timestamp("开始发送请求...", ">>> ")

        response = requests.post(
            url,
            json=data,
            stream=True,
            headers={"Content-Type": "application/json"},
            timeout=180
        )

        print_with_timestamp("连接建立，等待响应...\n", ">>> ")

        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                data_str = line[6:]
                try:
                    event = json.loads(data_str)
                    event_type = event.get('type', '')
                    current_time = f"{time.time() - start_time:.1f}s"

                    if event_type == 'start':
                        session_id = event.get('session_id', 'N/A')
                        print_with_timestamp(f"会话已创建: {session_id[:8]}...", "[START] ", True)
                        print()

                    elif event_type == 'thinking':
                        print_with_timestamp("Agent 正在分析问题...", "[THINK] ", True)

                    elif event_type == 'action':
                        tool_name = event.get('action', 'unknown')
                        print_with_timestamp(
                            f"决定调用工具: {tool_name}",
                            "[ACTION] ",
                            True
                        )

                    elif event_type == 'tool_start':
                        tool_count += 1
                        tool_name = event.get('tool', 'unknown')
                        print_with_timestamp(
                            f"正在调用第 {tool_count} 个工具: {tool_name}",
                            "[TOOL] ",
                            True
                        )
                        # 显示加载动画
                        for i in range(3):
                            sys.stdout.write(f"\r       {'. ' * (i + 1)}等待工具返回{'.' * (i + 1)}")
                            sys.stdout.flush()
                            time.sleep(0.2)
                        sys.stdout.write('\r' + ' ' * 60 + '\r')
                        sys.stdout.flush()

                    elif event_type == 'tool_end':
                        print_with_timestamp(
                            f"工具返回成功 [{current_time}]",
                            "[TOOL] ",
                            True
                        )
                        print()

                    elif event_type == 'done':
                        print_with_timestamp(
                            "Agent 完成分析，正在生成回答...",
                            "[DONE] ",
                            True
                        )
                        print("\n" + "-"*80)
                        print("最终回答:")
                        print("-"*80 + "\n")

                    elif event_type == 'final':
                        response_text = event.get('response', '')
                        # 打字机效果显示回答
                        for char in response_text:
                            sys.stdout.write(char)
                            sys.stdout.flush()
                            time.sleep(0.01)  # 打字机延迟
                        print("\n\n" + "-"*80)
                        session_id = event.get('session_id', session_id)

                    elif event_type == 'error':
                        print_with_timestamp(
                            f"错误: {event.get('error', '')}",
                            "[ERROR] ",
                            True
                        )

                except json.JSONDecodeError:
                    pass

        elapsed = time.time() - start_time
        print(f"\n总耗时: {elapsed:.2f} 秒")
        print(f"调用工具数: {tool_count}")
        print(f"Session ID: {session_id}")
        print("="*80)

    except requests.RequestException as e:
        print(f"\n请求失败: {e}")
    except KeyboardInterrupt:
        print("\n\n用户中断")

def test_comprehensive_analysis():
    """测试综合分析"""
    url = "http://127.0.0.1:8006/api/v1/chat/stream"

    print("\n" + "="*80)
    print("流式对话演示 - 综合分析（会调用多个工具）")
    print("="*80)
    print("\n问题: 分析一下 mobile-app 项目的整体健康状况\n")

    data = {
        "message": "分析一下 mobile-app 项目的整体健康状况",
        "session_id": None
    }

    start_time = time.time()
    tool_count = 0
    current_tool = None

    try:
        print_with_timestamp("开始发送请求...", ">>> ")

        response = requests.post(
            url,
            json=data,
            stream=True,
            headers={"Content-Type": "application/json"},
            timeout=300
        )

        print_with_timestamp("连接建立，开始流式接收...\n", ">>> ")

        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                data_str = line[6:]
                try:
                    event = json.loads(data_str)
                    event_type = event.get('type', '')
                    elapsed = time.time() - start_time

                    if event_type == 'start':
                        print_with_timestamp("会话创建成功", "[START] ", True)
                        print()

                    elif event_type == 'thinking':
                        print_with_timestamp("思考中...", "[THINK] ", True)

                    elif event_type == 'action':
                        tool_name = event.get('action', 'unknown')
                        current_tool = tool_name
                        print_with_timestamp(
                            f"准备调用: {tool_name}",
                            "[PLAN] ",
                            True
                        )

                    elif event_type == 'tool_start':
                        tool_count += 1
                        tool_name = event.get('tool', 'unknown')
                        print_with_timestamp(
                            f"工具 {tool_count}/5: {tool_name} 调用中... [{elapsed:.1f}s]",
                            "[EXEC] ",
                            True
                        )

                    elif event_type == 'tool_end':
                        print_with_timestamp(
                            f"✓ 完成 [{elapsed:.1f}s]",
                            "[DONE] ",
                            True
                        )

                    elif event_type == 'done':
                        print()
                        print_with_timestamp(
                            f"所有工具执行完毕，共调用 {tool_count} 个工具",
                            "[INFO] ",
                            True
                        )
                        print_with_timestamp(
                            "正在生成最终报告...",
                            "[GEN]  ",
                            True
                        )
                        print("\n" + "="*80)

                    elif event_type == 'final':
                        response_text = event.get('response', '')
                        print(response_text)
                        print("="*80)

                except json.JSONDecodeError:
                    pass

        total_time = time.time() - start_time
        print(f"\n总耗时: {total_time:.2f} 秒")
        print(f"平均每个工具: {total_time/max(tool_count, 1):.2f} 秒")
        print("="*80)

    except requests.RequestException as e:
        print(f"\n请求失败: {e}")
    except KeyboardInterrupt:
        print("\n\n用户中断")

if __name__ == "__main__":
    # 禁用 Python 输出缓冲
    sys.stdout.reconfigure(line_buffering=True)

    print("\n请选择测试场景:")
    print("1. 简单查询（1个工具）")
    print("2. 综合分析（5个工具）")
    print("3. 退出")

    try:
        choice = input("\n请输入选择 (1-3): ").strip()

        if choice == '1':
            test_single_query()
        elif choice == '2':
            test_comprehensive_analysis()
        elif choice == '3':
            print("退出")
        else:
            print("无效选择")

    except KeyboardInterrupt:
        print("\n\n已取消")
