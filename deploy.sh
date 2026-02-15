#!/bin/bash

#============================================
# NanoClaw API 一键部署脚本
#============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SERVICE_NAME")"
API_PORT="${API_PORT:-3456}"
API_HOST="${API_HOST:-0.0.0.0}"
SERVICE_NAME="nanoclaw-api"
LOG_DIR="/var/log/nanoclaw"

# 默认值
DEFAULT_API_KEY=""
DEFAULT_MODEL="claude-sonnet-4-20250514"

# 打印函数
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示帮助
show_help() {
    cat << EOF
用法: $0 [选项]

选项:
    --install         安装依赖并构建
    --start           启动服务
    --stop            停止服务
    --restart         重启服务
    --status          查看服务状态
    --enable          开机自启动
    --disable         取消开机自启动
    --deploy          完整部署 (install + enable + start)
    --uninstall       卸载服务
    -p, --port        设置端口 (默认: 3456)
    -h, --host        设置绑定地址 (默认: 0.0.0.0)
    -k, --key         设置 API 密钥
    --help            显示帮助

示例:
    $0 --deploy                           # 完整部署
    $0 --deploy -p 8080 -k my-secret     # 自定义端口和密钥
    $0 --install                          # 仅安装
    $0 --restart                          # 重启服务
EOF
}

# 检查 root 权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_warning "建议使用 root 权限运行 (sudo $0)"
    fi
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装"
        print_info "请先安装 Node.js: https://nodejs.org/"
        exit 1
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        print_error "npm 未安装"
        exit 1
    fi
    
    NODE_VERSION=$(node -v)
    print_success "Node.js $NODE_VERSION"
}

# 安装项目
install() {
    print_info "安装项目..."
    
    cd "$SCRIPT_DIR"
    
    # 安装依赖
    print_info "安装 npm 依赖..."
    npm install
    
    # 构建
    print_info "构建项目..."
    npm run build
    
    print_success "安装完成"
}

# 创建 systemd 服务
create_systemd_service() {
    print_info "创建 systemd 服务..."
    
    # 创建日志目录
    mkdir -p "$LOG_DIR"
    
    # 生成服务文件
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=NanoClaw API Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$SCRIPT_DIR
Environment=NODE_ENV=production
Environment=API_PORT=$API_PORT
Environment=API_HOST=$API_HOST
$([[ -n "$API_KEY" ]] && echo "Environment=NANOCLAW_API_KEY=$API_KEY")
ExecStart=$(which node) $SCRIPT_DIR/dist/index.js
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/stdout.log
StandardError=append:$LOG_DIR/stderr.log

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "systemd 服务已创建"
}

# 启动服务
start_service() {
    print_info "启动服务..."
    
    if command -v systemctl &> /dev/null; then
        systemctl start "$SERVICE_NAME"
        sleep 2
        
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            print_success "服务已启动"
        else
            print_error "服务启动失败"
            journalctl -u "$SERVICE_NAME" --no-pager -n 20
            exit 1
        fi
    else
        # 非 systemd 环境，直接启动
        cd "$SCRIPT_DIR"
        export API_PORT="$API_PORT"
        export API_HOST="$API_HOST"
        [[ -n "$API_KEY" ]] && export NANOCLAW_API_KEY="$API_KEY"
        
        nohup npm run start > "$LOG_DIR/stdout.log" 2>&1 &
        sleep 3
        print_success "服务已启动 (PID: $(pgrep -f 'node dist/index.js'))"
    fi
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    
    if command -v systemctl &> /dev/null; then
        systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    else
        pkill -f 'node dist/index.js' 2>/dev/null || true
    fi
    
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    stop_service
    sleep 1
    start_service
}

# 查看状态
status_service() {
    if command -v systemctl &> /dev/null; then
        systemctl status "$SERVICE_NAME" --no-pager
    else
        if pgrep -f 'node dist/index.js' > /dev/null; then
            print_success "服务运行中 (PID: $(pgrep -f 'node dist/index.js'))"
        else
            print_warning "服务未运行"
        fi
    fi
}

# 开机自启动
enable_service() {
    print_info "启用开机自启动..."
    
    if command -v systemctl &> /dev/null; then
        systemctl daemon-reload
        systemctl enable "$SERVICE_NAME"
        print_success "开机自启动已启用"
    else
        print_warning "systemd 未安装，无法设置开机自启动"
    fi
}

# 取消开机自启动
disable_service() {
    print_info "取消开机自启动..."
    
    if command -v systemctl &> /dev/null; then
        systemctl disable "$SERVICE_NAME" 2>/dev/null || true
        print_success "开机自启动已取消"
    fi
}

# 卸载服务
uninstall() {
    print_warning "卸载服务..."
    
    stop_service
    disable_service
    
    # 删除服务文件
    rm -f /etc/systemd/system/${SERVICE_NAME}.service
    
    print_success "服务已卸载"
    print_info "如需完全清理，可手动删除项目目录: $SCRIPT_DIR"
}

# 部署
deploy() {
    print_info "开始部署..."
    
    check_dependencies
    install
    create_systemd_service
    enable_service
    start_service
    
    print_success "部署完成!"
    print_info "服务地址: http://$([ "$API_HOST" = "0.0.0.0" ] && hostname -I | awk '{print $1}' || echo "$API_HOST"):$API_PORT"
    
    if [[ -n "$API_KEY" ]]; then
        print_info "API 密钥: $API_KEY"
    fi
}

# 解析参数
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --install)
            ACTION="install"
            shift
            ;;
        --start)
            ACTION="start"
            shift
            ;;
        --stop)
            ACTION="stop"
            shift
            ;;
        --restart)
            ACTION="restart"
            shift
            ;;
        --status)
            ACTION="status"
            shift
            ;;
        --enable)
            ACTION="enable"
            shift
            ;;
        --disable)
            ACTION="disable"
            shift
            ;;
        --deploy)
            ACTION="deploy"
            shift
            ;;
        --uninstall)
            ACTION="uninstall"
            shift
            ;;
        -p|--port)
            API_PORT="$2"
            shift 2
            ;;
        -h|--host)
            API_HOST="$2"
            shift 2
            ;;
        -k|--key)
            API_KEY="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 默认操作
ACTION="${ACTION:-deploy}"

# 执行
case "$ACTION" in
    install)
        check_dependencies
        install
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    enable)
        check_root
        enable_service
        ;;
    disable)
        check_root
        disable_service
        ;;
    deploy)
        check_root
        deploy
        ;;
    uninstall)
        check_root
        uninstall
        ;;
esac
