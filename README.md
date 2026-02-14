 # RAGWorkProject 快速部署指南

本指南提供一条最短路径：在同一台服务器上启动后端 API，并将前端静态站点部署到 Nginx。

## 0. 环境前置

- Node.js >= 20
- Python >= 3.10
- Nginx

## 1. 启动后端 API

```bash
cd /root/workspace/RAGWorkProject/backend

# 如需配置模型与密钥，请先编辑：
# /root/workspace/RAGWorkProject/config/backend.yaml

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python run_api.py
```

健康检查：

```bash
curl -fsS http://127.0.0.1:8000/health
```

## 2. 构建前端静态文件

```bash
cd /root/workspace/bnu-demo
npm install

# 确认 API 地址
# /root/workspace/bnu-demo/docusaurus.config.ts -> customFields.apiBaseUrl

npm run build
```

构建产物位于：

```
/root/workspace/bnu-demo/build
```

## 3. 部署到 Nginx

将静态文件拷贝到 Nginx 可访问目录：

```bash
sudo mkdir -p /var/www/bnurag
sudo cp -r /root/workspace/bnu-demo/build/* /var/www/bnurag/
sudo chown -R www-data:www-data /var/www/bnurag
sudo chmod -R 755 /var/www/bnurag
```

创建 Nginx 配置：

```bash
sudo nano /etc/nginx/sites-available/bnurag
```

写入：

```nginx
server {
	listen 80;
	server_name xxx.xxx.xxx.xxx;  # 改为你的公网 IP 或域名

	location /bnurag/ {
		alias /var/www/bnurag/;
		index index.html;
		try_files $uri $uri/ /bnurag/index.html;
	}
}
```

启用并重载：

```bash
sudo ln -s /etc/nginx/sites-available/bnurag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

访问：

```
http://xxx.xxx.xxx.xxx/bnurag/
```

## 4. 常见问题

- 403 Forbidden: 不要将 Nginx root 指向 /root 目录，改用 /var/www。
- 无法对话: 确认后端已启动且 CORS 允许你的前端来源。
- 图片不显示: 确认后端已启用 /api/assets/image 并重启服务。
