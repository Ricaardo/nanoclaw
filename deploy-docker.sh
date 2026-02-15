#!/bin/bash

#============================================
# NanoClaw API Docker 一键部署脚本
#============================================

set -e

# 配置变量
API_PORT="${API_PORT:-3456}"
API_KEY="${API_KEY:-}"
CONTAINER_NAME="nanoclaw-api"
IMAGE_NAME="nanoclaw-api:latest"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    cat << EOF
用法: $0 [命令] [选项]

命令:
    install     安装并构建 Docker 镜像
    start       启动容器
    stop        停止容器
    restart     重启容器
    logs        查看日志
    status      查看状态
    deploy      完整部署
    remove      删除容器和镜像

选项:
    -p, --port      端口 (默认: 3456)
    -k, --key       API 密钥

示例:
    $0 deploy                    # 完整部署
    $0 deploy -p 8080 -k secret  # 自定义端口和密钥
    $0 logs                      # 查看日志
EOF
}

# 获取本机 IP
get_local_ip() {
    if command -v ip &> /dev/null; then
        ip route get 1 | awk '{print $(NF-2)}'
    elif command -v ifconfig &> /dev/null; then
        ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1
    else
        echo "localhost"
    fi
}

# 构建镜像
install() {
    print_info "构建 Docker 镜像..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"
    
    # 检查 Dockerfile
    if [[ ! -f "Dockerfile.api" ]]; then
        print_info "创建 Dockerfile..."
        cat > Dockerfile.api << 'DOCKERFILE'
FROM node:20-alpine

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm install

# 构建
COPY . .
RUN npm run build

# 暴露端口
EXPOSE 3456

# 启动
CMD ["node", "dist/index.js"]
DOCKERFILE
    fi
    
    docker build -f Dockerfile.api -t "$IMAGE_NAME" .
    print_success "镜像构建完成"
}

# 启动
start() {
    print_info "启动容器..."
    
    # 检查镜像
    if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
        print_error "镜像不存在，请先运行: $0 install"
        exit 1
    fi
    
    # 停止旧容器
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    
    # 构建启动命令
    DOCKER_CMD="docker run -d \\
        --name $CONTAINER_NAME \\
        -p $API_PORT:3456 \\
        -e API_PORT=3456 \\
        -e API_HOST=0.0.0.0"
    
    if [[ -n "$API_KEY" ]]; then
        DOCKER_CMD="$DOCKER_CMD \\
        -e NANOCLAW_API_KEY=$API_KEY"
    fi
    
    DOCKER_CMD="$DOCKER_CMD \\
        --restart=always \\
        $IMAGE_NAME"
    
    eval "$DOCKER_CMD"
    
    sleep 2
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        print_success "容器已启动"
        print_info "访问地址: http://$(get_local_ip):$API_PORT"
    else
        print_error "启动失败"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
}

# 停止
stop() {
    print_info "停止容器..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    print_success "容器已停止"
}

# 重启
restart() {
    stop
    start
}

# 日志
logs() {
    docker logs -f --tail 100 "$CONTAINER_NAME"
}

# 状态
status() {
    if docker ps | grep -q "$CONTAINER_NAME"; then
        print_success "容器运行中"
        docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        print_warning "容器未运行"
    fi
}

# 部署
deploy() {
    install
    start
    print_success "部署完成!"
}

# 删除
remove() {
    print_warning "删除容器和镜像..."
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    docker rmi "$IMAGE_NAME" 2>/dev/null || true
    print_success "已删除"
}

# 参数解析
COMMAND="${1:-deploy}"

case "$COMMAND" in
    install)
        install
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    deploy)
        deploy
        ;;
    remove)
        remove
        ;;
    -h|--help)
        show_help
        ;;
    *)
        # 解析选项
        shift
        while [[ $# -gt 0 ]]; do
            case $1 in
                -p|--port)
                    API_PORT="$2"
                    shift 2
                    ;;
                -k|--key)
                    API_KEY="$2"
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done
        deploy
        ;;
esac
