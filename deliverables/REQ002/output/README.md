# NAS File Manager MCP Server

NAS 文件管理 MCP Server，通过 SSE 传输层提供 7 个文件操作工具，供 OpenClaw 等 AI 客户端调用。

## 功能

- **list_directory** - 列出目录内容（文件名、类型、大小），支持递归
- **read_file** - 读取文件文本内容
- **write_file** - 写入文件内容，自动创建父目录
- **delete_file** - 删除文件
- **create_directory** - 创建目录，支持递归创建父目录
- **delete_directory** - 删除目录，支持递归删除
- **move_file** - 移动文件或目录

## 安装

### 环境要求

- Python 3.10+
- pip

### 安装步骤

```bash
# 克隆项目
git clone <repo-url>
cd nas-mcp-server

# 安装依赖
pip install -e .

# 安装开发依赖（可选）
pip install -e ".[dev]"
```

## 配置

通过环境变量配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| NAS_ROOT_DIR | 文件操作根目录（沙箱边界） | /data |
| MCP_HOST | 监听地址 | 0.0.0.0 |
| MCP_PORT | 监听端口 | 8080 |

## 启动

```bash
# 直接运行
nas-mcp-server

# 或通过 Python 模块
python -m nas_mcp_server

# 指定根目录和端口
NAS_ROOT_DIR=/mnt/nas MCP_PORT=9090 nas-mcp-server
```

## OpenClaw 集成

### 通过 SkillHub 安装

项目根目录包含 `manifest.json`，符合 SkillHub 规范。OpenClaw 可通过以下方式发现并连接：

1. 在 OpenClaw 中添加 MCP Server
2. 选择 SSE 传输方式
3. 填入 Server 地址：`http://<NAS_IP>:8080/sse`

### 手动配置

在 OpenClaw 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "nas-file-manager": {
      "transport": "sse",
      "url": "http://<NAS_IP>:8080/sse"
    }
  }
}
```

## 安全说明

- 所有文件操作限制在 `NAS_ROOT_DIR` 指定的根目录内
- 路径穿越攻击（如 `../`）会被自动拦截
- 建议仅在内网环境使用，不要暴露到公网

## 测试

```bash
pip install -e ".[dev]"
pytest
```

## 部署到极空间 Z4Pro

### 1. 安装 Python

极空间 Z4Pro 基于 Linux，确保系统已安装 Python 3.10+：

```bash
python3 --version
# 如果版本低于 3.10，需要手动编译安装或通过包管理器升级
```

### 2. 上传项目文件

将项目文件上传到 NAS，例如 `/opt/nas-mcp-server-src/`：

```bash
# 通过 scp 上传
scp -r . user@<NAS_IP>:/opt/nas-mcp-server-src/
```

### 3. 运行安装脚本

```bash
cd /opt/nas-mcp-server-src
bash deploy/install.sh /opt/nas-mcp-server
```

安装脚本会自动完成：
- 创建 Python 虚拟环境
- 安装项目依赖
- 复制配置文件模板

### 4. 配置环境变量

编辑 `/opt/nas-mcp-server/.env`：

```bash
vi /opt/nas-mcp-server/.env
```

必须修改的配置项：

```ini
# 设置为 NAS 上实际的文件共享目录
NAS_ROOT_DIR=/mnt/nas/shared

# 服务端口（默认 8080，按需修改）
MCP_PORT=8080
```

### 5. 手动启动测试

```bash
cd /opt/nas-mcp-server
chmod +x start.sh
./start.sh
```

验证服务正常运行后，按 Ctrl+C 停止。

### 6. 注册 systemd 服务

```bash
# 创建服务用户（可选，增强安全性）
sudo useradd -r -s /sbin/nologin nas-mcp

# 设置目录权限
sudo chown -R nas-mcp:nas-mcp /opt/nas-mcp-server

# 安装 service 文件
sudo cp deploy/nas-mcp-server.service /etc/systemd/system/
sudo systemctl daemon-reload

# 启动并设置开机自启
sudo systemctl enable --now nas-mcp-server

# 查看状态
sudo systemctl status nas-mcp-server
```

### 7. 验证部署

```bash
# 检查服务状态
sudo systemctl status nas-mcp-server

# 查看日志
sudo journalctl -u nas-mcp-server -f

# 测试 SSE 连接
curl -N http://localhost:8080/sse
```

### 常见问题排查

| 问题 | 排查方法 |
|------|---------|
| 服务启动失败 | `journalctl -u nas-mcp-server -e` 查看错误日志 |
| 端口被占用 | `ss -tlnp \| grep 8080`，修改 .env 中的 MCP_PORT |
| Python 版本不对 | 确认 .venv 使用的 Python >= 3.10 |
| 权限不足 | 确认 nas-mcp 用户对 NAS_ROOT_DIR 有读写权限 |
| 路径穿越被拒绝 | 正常安全行为，所有操作限制在 NAS_ROOT_DIR 内 |
| 连接超时 | 检查防火墙是否放行 MCP_PORT 端口 |
