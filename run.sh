#!/bin/bash
#
# Data Agent 启动脚本
#

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查 Python 版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        error "未找到 Python，请先安装 Python 3.10+"
    fi

    # 检查版本
    VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    MAJOR=$(echo $VERSION | cut -d. -f1)
    MINOR=$(echo $VERSION | cut -d. -f2)

    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
        error "Python 版本需要 3.10+，当前版本: $VERSION"
    fi

    info "Python 版本: $VERSION"
}

# 检查并激活虚拟环境
activate_venv() {
    if [ -d ".venv" ]; then
        info "激活虚拟环境..."
        source .venv/bin/activate
    else
        warn "未找到虚拟环境，创建中..."
        $PYTHON_CMD -m venv .venv
        source .venv/bin/activate
        info "安装依赖..."
        pip install -e . -q
    fi
}

# 检查 .env 文件
check_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            warn ".env 文件不存在，从 .env.example 复制..."
            cp .env.example .env
            warn "请编辑 .env 文件配置 API 密钥"
        else
            warn ".env 文件不存在，部分功能可能不可用"
        fi
    fi
}

# 主函数
main() {
    echo "======================================"
    echo "       Data Agent 启动脚本"
    echo "======================================"
    echo

    check_python
    activate_venv
    check_env

    echo
    info "启动 Data Agent..."
    echo

    # 启动应用
    python -m data_agent.main "$@"
}

# 运行
main "$@"
