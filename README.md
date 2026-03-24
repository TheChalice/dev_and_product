# 1. 安装依赖
pip install fastapi uvicorn httpx python-multipart

# 2. 配置API Key (请在终端执行，替换为你的真实Key)
# Windows: set DASHSCOPE_API_KEY="sk-你的密钥"
# Mac/Linux: export DASHSCOPE_API_KEY="sk-你的密钥"

# 3. 运行后端服务
uvicorn main:app --reload

# 4. 启动前端
# 直接在浏览器打开 index.html 文件即可


# 测试
产品视角输入示例
输入：“我们要做一个‘双11’的预售活动，用户支付定金后，订单要锁定库存，尾款支付后才能发货，这个逻辑怎么实现？”
开发视角输入示例
输入：“刚才线上服务报错了，是因为 Redis 集群的一个节点内存满了，触发了 OOM，导致部分用户的 Session 丢失，现在重启了服务。”
