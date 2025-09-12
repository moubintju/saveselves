#!/usr/bin/env python3
"""
简单的依赖安装脚本
适用于Windows环境，避免编译问题
"""
import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        print(f"正在安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {package} 安装失败: {e}")
        return False

def main():
    """主安装流程"""
    print("开始安装A股筛选工具的依赖包...")
    print("=" * 50)
    
    # 基础包列表（避免版本冲突）
    packages = [
        "flask",
        "requests", 
        "akshare",
        "openpyxl"
    ]
    
    # 尝试安装pandas和numpy（可能需要预编译版本）
    complex_packages = [
        "pandas",
        "numpy"
    ]
    
    # 安装基础包
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    # 尝试安装复杂包
    for package in complex_packages:
        if install_package(package):
            success_count += 1
    
    print("=" * 50)
    print(f"安装完成！成功安装 {success_count} 个包")
    
    if success_count >= 4:  # 至少安装了基本包
        print("✓ 基本环境配置完成，可以尝试运行程序")
        print("  运行命令: python main.py")
    else:
        print("✗ 部分包安装失败，请检查网络连接和Python环境")

if __name__ == "__main__":
    main()