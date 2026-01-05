#!/bin/bash
# DevOps Agent 服务器端部署脚本
# 用于在公司服务器上加载和运行 Docker 镜像

set -e

echo "=========================================="
echo "DevOps Agent 服务器部署工具"
echo "=========================================="
echo ""

# 配置
IMAGE_NAME="devops-agent:production"
WORK_DIR="/opt/devops-agent"
TAR_FILE="/tmp/devops-agent.tar.gz"
CONTAINER_NAME="devops-agent"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 tar 文件是否存在
if [ ! -f "$TAR_FILE" ]; then
    echo -e "${RED}❌ 错误: 镜像文件不存在: $TAR_FILE${NC}"
    echo "请先使用 WinSCP/scp 上传镜像文件到 /tmp/"
    exit 1
fi

# 1. 加载镜像
echo -e "${YELLOW}📦 步骤 1: 加载 Docker 镜像...${NC}"
gunzip < "$TAR_FILE" | docker load
echo -e "${GREEN}✅ 镜像加载完成${NC}"

# 2. 创建工作目录
echo ""
echo -e "${YELLOW}📁 步骤 2: 创建工作目录...${NC}"
mkdir -p "$WORK_DIR"/{data,logs}
cd "$WORK_DIR"
echo -e "${GREEN}✅ 工作目录: $WORK_DIR${NC}"

# 3. 检查并创建 .env 文件
echo ""
echo -e "${YELLOW}⚙️ 步骤 3: 检查环境配置...${NC}"
if [ ! -f "$WORK_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  .env 文件不存在，创建模板...${NC}"
    cat > "$WORK_DIR/.env" << 'EOF'
# LLM 配置 - 公司 Higress 网关
DEEPSEEK_API_KEY=610b268c-a36e-4a47-a8ed-386787eb26af
DEEPSEEK_BASE_URL=https://higress.devops.ecp.digitalvolvo.com/gateway/v1/chat/completions
DEEPSEEK_MODEL=deepseek-reasoner

# 数据库配置
DATABASE_URL=sqlite:///./data/devops_agent.db
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=dhuci_agent_db

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# 日志配置
LOG_LEVEL=INFO
EOF
    chmod 600 "$WORK_DIR/.env"
    echo -e "${GREEN}✅ .env 文件已创建${NC}"
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

# 4. 停止旧容器
echo ""
echo -e "${YELLOW}🛑 步骤 4: 停止旧容器...${NC}"
if docker ps -a | grep -q "$CONTAINER_NAME"; then
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo -e "${GREEN}✅ 旧容器已清理${NC}"
else
    echo -e "${GREEN}✅ 无需清理${NC}"
fi

# 5. 启动新容器
echo ""
echo -e "${YELLOW}🚀 步骤 5: 启动新容器...${NC}"
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file "$WORK_DIR/.env" \
  -v "$WORK_DIR/data":/app/data \
  -v "$WORK_DIR/logs":/app/logs \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  "$IMAGE_NAME"

echo -e "${GREEN}✅ 容器已启动${NC}"

# 6. 等待服务启动
echo ""
echo -e "${YELLOW}⏳ 步骤 6: 等待服务启动（5秒）...${NC}"
sleep 5

# 7. 健康检查
echo ""
echo -e "${YELLOW}🏥 步骤 7: 健康检查...${NC}"
if curl -f -s http://localhost:8000/api/v1/health > /dev/null; then
    echo -e "${GREEN}✅ 服务健康检查通过${NC}"
else
    echo -e "${RED}⚠️  健康检查失败，请查看日志${NC}"
fi

# 8. 显示容器状态
echo ""
echo -e "${YELLOW}📊 容器状态:${NC}"
docker ps | grep "$CONTAINER_NAME"

# 9. 清理临时文件
echo ""
echo -e "${YELLOW}🧹 步骤 8: 清理临时文件...${NC}"
rm -f "$TAR_FILE"
echo -e "${GREEN}✅ 临时文件已清理${NC}"

# 10. 完成
echo ""
echo "=========================================="
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}📋 常用命令:${NC}"
echo "  查看日志:   docker logs -f $CONTAINER_NAME"
echo "  停止服务:   docker stop $CONTAINER_NAME"
echo "  重启服务:   docker restart $CONTAINER_NAME"
echo "  查看状态:   docker ps | grep $CONTAINER_NAME"
echo ""
echo -e "${YELLOW}🔗 API 端点:${NC}"
echo "  健康检查:   http://localhost:8000/api/v1/health"
echo "  API 文档:   http://localhost:8000/docs"
echo "  聊天接口:   http://localhost:8000/api/v1/chat/stream"
echo ""
echo -e "${YELLOW}💡 提示:${NC}"
echo "  如需修改配置，编辑 $WORK_DIR/.env 后重启容器"
echo ""
