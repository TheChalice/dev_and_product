from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse  # 1. 必须导入这个！
from pydantic import BaseModel
from typing import AsyncGenerator
import httpx
import os
import json

app = FastAPI(title="沟通翻译助手 Agent")

# --- 配置 API Key ---
API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not API_KEY:
    # 为了调试方便，如果没有环境变量，可以在这里临时填入（不推荐生产环境）
    # API_KEY = "sk-your-key-here" 
    pass 

DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL_NAME = "qwen-plus"

# --- 提示词模板 ---
SYSTEM_PROMPTS = {
    "product_to_dev": """你是一位拥有10年经验的全栈架构师。请将产品经理的业务需求转化为技术语言。
**任务要求：**
1. **识别意图**：提炼核心的技术目标。
2. **方案建议**：推荐具体的算法、技术栈。
3. **数据指标**：指出需要的数据源和性能指标。
4. **风险补充**：指出需求中缺失的关键信息。
**输出格式：**
- **🎯 技术目标**：...
- **🛠️ 实现方案**：...
- **⚠️ 待确认**：...""",

    "dev_to_product": """你是一位拥有10年经验的首席产品官(CPO)。请将工程师的技术方案转化为商业语言。
**任务要求：**
1. **价值映射**：将技术参数映射到用户体验。
2. **业务影响**：说明支持的业务规模。
3. **通俗解释**：用比喻解释复杂概念。
**输出格式：**
- **🚀 用户体验**：...
- **📈 业务增长**：...
- **💡 核心价值**：..."""
}

# --- 数据模型 ---
class TranslationRequest(BaseModel):
    text: str
    direction: str

# --- 核心逻辑 ---
@app.post("/translate")
async def translate(request: TranslationRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="输入文本不能为空")

    if request.direction not in SYSTEM_PROMPTS:
        raise HTTPException(status_code=400, detail="方向错误")

    system_msg = SYSTEM_PROMPTS[request.direction]
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": request.text}
    ]

    # 2. 定义生成器函数
    async def generate():
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": True,
            "temperature": 0.7
        }

        try:
            # 使用 httpx 异步客户端
            async with httpx.AsyncClient(timeout=60.0) as client:
                # 注意：httpx 的 stream 方法处理流式 POST
                async with client.stream("POST", DASHSCOPE_URL, json=data, headers=headers) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield f"data: {json.dumps({'error': error_text.decode()})}\n\n"
                        return

                    # 3. 逐块读取并转发
                    async for chunk in response.aiter_bytes():
                        # 确保 chunk 是字符串
                        line = chunk.decode("utf-8")
                        # 阿里云 DashScope 兼容模式通常直接返回 data: {...} 格式
                        # 如果是纯 JSON，需要手动包装成 SSE 格式
                        if line.strip().startswith("data:"):
                             yield f"{line}\n\n"
                        else:
                             yield f"data: {line}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    # 4. 返回流式响应
    return StreamingResponse(generate(), media_type="text/event-stream")

# --- 其他配置 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)