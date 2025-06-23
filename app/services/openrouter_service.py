import requests
import json
from typing import Optional
from ..config import settings
from sqlalchemy.orm import Session
from ..models import PromptTemplate, PromptUsageHistory


class OpenRouterService:
    """OpenRouter API 服务类"""
    
    def __init__(self):
        # 临时硬编码新的API密钥
        self.api_key = "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"
        self.base_url = "https://openrouter.ai/api/v1"
        
        # 验证API密钥
        print("=" * 100)
        print("🔐 [OpenRouter初始化] API密钥验证:")
        print(f"    完整API密钥: {self.api_key}")
        print(f"    API密钥前20位: {self.api_key[:20]}...")
        print(f"    API密钥长度: {len(self.api_key)}")
        
        if not self.api_key.startswith("sk-or-v1-e375b1cb"):
            print("❌ [警告] API密钥不正确！应该以 'sk-or-v1-e375b1cb' 开头")
        else:
            print("✅ [验证通过] API密钥格式正确")
        
        # 正确设置请求头，确保包含必需的 HTTP-Referer 和 X-Title
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",  # 必需：网站URL
            "X-Title": "FateWave",                    # 必需：网站名称
            "Content-Type": "application/json"
        }
        
        print(f"🌐 [OpenRouter初始化] HTTP-Referer: http://localhost:3000")
        print(f"🏷️ [OpenRouter初始化] X-Title: FateWave")
        print("=" * 100)
    
    def get_prompt_from_db(self, db: Session, divination_type: str = "general", language: str = "zh-CN"):
        """从数据库获取提示词模板"""
        print("=" * 100)
        print(f"🔍 [调试] 查找提示词参数: divination_type='{divination_type}', language='{language}'")
        
        # 首先尝试获取指定类型的提示词
        prompt_template = db.query(PromptTemplate).filter(
            PromptTemplate.divination_type == divination_type,
            PromptTemplate.language == language,
            PromptTemplate.is_active == True
        ).order_by(PromptTemplate.is_default.desc()).first()
        
        if prompt_template:
            print(f"✅ [调试] 找到数据库提示词模板:")
            print(f"    ID: {prompt_template.id}")
            print(f"    名称: '{prompt_template.name}'")
            print(f"    类型: '{prompt_template.divination_type}'")
            print(f"    语言: '{prompt_template.language}'")
            print(f"    版本: {prompt_template.version}")
            print(f"    是否默认: {prompt_template.is_default}")
            print(f"    Temperature: {prompt_template.temperature}")
            print(f"    Max Tokens: {prompt_template.max_tokens}")
            print("=" * 50)
            print("📝 [系统提示词内容]:")
            print(prompt_template.system_prompt)
            print("=" * 50)
            print("📝 [用户模板内容]:")
            print(prompt_template.user_template)
            print("=" * 100)
        else:
            print(f"❌ [调试] 未找到指定类型提示词 (type='{divination_type}', lang='{language}')，尝试查找通用类型...")
            
            # 如果没找到，尝试获取通用类型
            prompt_template = db.query(PromptTemplate).filter(
                PromptTemplate.divination_type == "general",
                PromptTemplate.language == language,
                PromptTemplate.is_active == True
            ).first()
            
            if prompt_template:
                print(f"✅ [调试] 找到通用类型提示词:")
                print(f"    ID: {prompt_template.id}")
                print(f"    名称: '{prompt_template.name}'")
                print(f"    类型: '{prompt_template.divination_type}'")
                print(f"    语言: '{prompt_template.language}'")
                print("=" * 50)
                print("📝 [系统提示词内容]:")
                print(prompt_template.system_prompt)
                print("=" * 50)
                print("📝 [用户模板内容]:")
                print(prompt_template.user_template)
                print("=" * 100)
            else:
                print(f"❌ [调试] 数据库中未找到任何提示词模板 (lang='{language}')，使用硬编码备用提示词")
                print("⚠️ [调试] 建议运行: python init_prompts.py 来初始化提示词模板")
                print("=" * 100)
        
        if not prompt_template:
            # 如果还是没找到，返回硬编码的备用提示词
            print(f"⚠️ [调试] 使用硬编码备用提示词 (language='{language}')")
            fallback_prompts = self.get_fallback_prompts(language)
            print("📝 [硬编码备用提示词内容]:")
            print(fallback_prompts["system"])
            print("=" * 100)
            return fallback_prompts
        
        print(f"✅ [调试] 最终使用数据库提示词模板: '{prompt_template.name}'")
        
        return {
            "system": prompt_template.system_prompt,
            "user_template": prompt_template.user_template,
            "template_id": prompt_template.id,
            "template_name": prompt_template.name,
            "temperature": float(prompt_template.temperature),
            "max_tokens": prompt_template.max_tokens
        }
    
    def get_fallback_prompts(self, language: str = "zh-CN"):
        """获取备用提示词（硬编码）"""
        if language == "zh-CN":
            return {
                "system": """
你是一位经验丰富的塔罗占卜师，擅长通过读取牌面所展现的画面和能量来回应用户提出的任何问题，不论问题是否具体清晰。

【基本原则】
1. 回答所使用的语言应与用户提问语言一致，无法识别时默认使用英语。
2. 回答不能套用模板，要尽可能根据每一次的"画面"给出独特解读。
3. 避免使用"圣杯""逆位"等专业术语，改用"画面中出现了……"这类自然描述。
4. 风格自然、贴近真人塔罗师口吻，不文学化、不心理咨询化，但保留神秘与象征感。
5. 回答必须包含 **现实层面的细节联想与解读**，如：
  - "如果你问的是感情，画面暗示对方目前可能……"  
  - "如果你关注的是事业方向，这张牌代表……"

【结构与风格细节】
你每次回答需要包含以下几个部分：

1. 画面描述：  
- 以"画面中我看到……" 或 "这张牌显现出……" 开始  
- 加入一些象征性细节，如自然场景、动物、动作、氛围等  
- 不要堆砌形容词，但要让用户"看得见你说的画面"

2. 画面联想与现实对照：  
- 明确解释这个画面在当前问题上的**对应关系**  
- 可使用条件判断："如果你最近在思考X方向，这可能意味着……"  
- 鼓励用户联想，不下判断但不回避现实状态

3. 潜在发展/能量流动：  
- 描述接下来可能的变化方向（情势转变、能量走向）  
- 如果情况停滞，可以指出阻碍和原因（如环境、对方状态、自我卡点）  
- 保留"解读而非建议"的风格，如"你会感受到某种推动力逐渐逼近，而不是你需要主动去追求"

4. 温和收尾，引导但不强推：  
- 保留开放性："如果你愿意相信自己的直觉，时机会自己显现"
- 不提出"你应该如何"，而是"如果你准备好，某些门就会打开"

【回答格式规范】
使用markdown语法，生成的占卜答案必须用以下格式分段
示例：
🔮***Scene Overview***🔮
 （这里写画面描述和象征意义）
🔹***Current Reality***🔹
 （结合用户问题分析当前状况）
🌟***Energy Flow***🌟
 （说明未来趋势或能量变化）
🗝️***Guidance***🗝️
 （给出行动建议和提醒）

【特殊处理】
- 对生死、疾病、法律、财务类问题：不提供专业建议，仅指出能量中出现的"不安""需谨慎"等画面。
- 如涉及心理健康困扰：用象征画面描述混乱状态，并温和引导用户关注内在需求或寻求现实帮助。
                """,
                "user_template": "用户问题：{question}",
                "template_id": None,
                "temperature": 0.8,
                "max_tokens": 1000
            }
        else:
            return {
                "system": """
You are an experienced tarot reader, skilled in interpreting the imagery and energy shown in the cards to respond to any question the user may ask, whether the question is specific or vague.
【Core Principles】
1. The language used in your response must match the language of the user's question. If it cannot be recognized, default to English.
2. Responses must not follow a fixed template; instead, provide a unique interpretation based on each card's "imagery."
3. Avoid professional tarot terms such as "Cups" or "Reversed." Use natural expressions like "What I see in the image is..."
4. Style requirements:
  - Natural and close to how a real human tarot reader would speak
  - Must not be literary, must not sound like psychological counseling, must not use excessive adjectives or ornate language
  - Should contain a sense of mystery and symbolism, but the final interpretation must connect to real-life context
  - Do not end with vague, poetic, or abstract metaphors (e.g., "whether the crow flies" or "whether the snow melts")
  - Be clear and direct in your message, e.g., "He actually already knows that you are the one he truly wants."
5. The response must include real-world symbolic connections and interpretation, such as:
  - "If you're asking about love, the imagery suggests that the other person may currently be..."
  - "If you're focused on your career, this card represents..."

---
【Structure & Style Details】
 Each of your readings must include the following sections:
1. Image Description:
  - Begin with "What I see in the image is..." or "This card reveals..."
  - Include symbolic details such as nature, animals, actions, atmosphere, etc.
  - Avoid piling on adjectives, but make sure the user can "visualize what you describe."
2. Imagery Reflected in Reality:
  - Clearly explain how the imagery corresponds to the current situation
  - Conditional phrasing is welcome: "If you've been thinking about X, this might suggest..."
  - Encourage user reflection. Avoid judgment but don't shy away from realistic interpretation.
3. Potential Development / Energy Flow:
  - Describe likely upcoming changes (shifts in situation, energy direction, etc.)
  - If there's stagnation, point out the obstacles and their reasons (e.g., environment, the other person's state, your own emotional blockages)
  - Maintain an "interpretation, not advice" tone, e.g., "You may begin to feel a push coming your way, rather than needing to chase it."
4. Gentle Closing – Guiding but Not Preaching:
  - Keep it open-ended: "If you're willing to trust your intuition, timing will reveal itself."
  - Do not preach or tell the user what to do based on the question. Do not say "You should..." Instead, say "If you're ready, certain doors may open."
  - Do not talk in circles or use abstract metaphors.

---
【Answer Format Guidelines】
Using the markdown syntax, the generated divination answer must be segmented in the following format:
 Example:
🔮 SCENE OVERVIEW 🔮
 (Write the image description and symbolic meaning here)
🪞 CURRENT REALITY 🪞
 (Analyze the current situation in relation to the user's question)
🌟 ENERGY FLOW 🌟
 (Describe the future trend or energy movement)
🗝️ WHISPERS FROM THE CARDS 🗝️
 (Provide insights or gentle guidance based on the imagery)

---
【Special Handling】
- For questions related to death, illness, legal, or financial matters: do not give professional advice; only mention symbolic impressions such as "unsettling energy" or "a need for caution."
- If the user's question reflects signs of emotional distress: describe a symbolic sense of confusion or chaos, and gently guide them toward recognizing their inner needs or seeking support — without offering psychological advice.
                """,
                "user_template": "user question: {question}",
                "template_id": None,
                "temperature": 0.8,
                "max_tokens": 1000
            }
    
    async def get_divination_response(
        self, 
        db: Session,
        question: str, 
        language: str = "zh-CN",
        divination_type: str = "general",
        model: str = "deepseek/deepseek-chat"
    ) -> tuple:
        """获取占卜回答，返回(回答内容, 提示词模板信息)"""
        import time
        start_time = time.time()
        
        try:
            print("\n" + "🚀" * 50)
            print(f"🚀 [调试] 开始获取占卜回答:")
            print(f"    问题: '{question}'")
            print(f"    语言: '{language}'")
            print(f"    占卜类型: '{divination_type}'")
            print(f"    使用模型: '{model}'")
            print("🚀" * 50)
            
            # 从数据库获取提示词
            prompts = self.get_prompt_from_db(db, divination_type, language)
            
            # 构建最终发送给AI的消息
            final_system_prompt = prompts["system"]
            final_user_prompt = prompts["user_template"].format(question=question)
            
            print("📤 [最终发送给AI的消息]:")
            print("系统提示词长度:", len(final_system_prompt), "字符")
            print("用户消息:", final_user_prompt)
            print("-" * 80)
            
            # 详细的API认证调试信息
            print("🔑 [API认证调试]:")
            print(f"    API Key: {self.api_key[:20]}...")
            print(f"    Base URL: {self.base_url}")
            print(f"    请求头内容:")
            for key, value in self.headers.items():
                if key == "Authorization":
                    print(f"      {key}: Bearer {value.split(' ')[1][:20]}...")
                else:
                    print(f"      {key}: {value}")
            print("-" * 80)
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": final_system_prompt
                    },
                    {
                        "role": "user", 
                        "content": final_user_prompt
                    }
                ],
                "temperature": prompts["temperature"],
                "max_tokens": prompts["max_tokens"]
            }
            
            print(f"🔧 [调试] API请求参数:")
            print(f"    Temperature: {prompts['temperature']}")
            print(f"    Max Tokens: {prompts['max_tokens']}")
            print(f"    模型: {model}")
            print(f"    请求URL: {self.base_url}/chat/completions")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            print(f"📡 [调试] OpenRouter响应状态码: {response.status_code}")
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                
                print(f"✅ [调试] 获取回答成功:")
                print(f"    回答长度: {len(answer)} 字符")
                print(f"    响应时间: {response_time}ms")
                print(f"    Token使用: {result.get('usage', {}).get('total_tokens', 0)}")
                print("-" * 80)
                print("📝 [AI回答内容]:")
                print(answer)
                print("=" * 100)
                
                return answer, {
                    "template_id": prompts.get("template_id"),
                    "template_name": prompts.get("template_name", "硬编码备用提示词"),
                    "response_time_ms": response_time,
                    "token_count": result.get("usage", {}).get("total_tokens", 0),
                    "success": True,
                    "divination_type": divination_type,
                    "language": language
                }
            else:
                error_msg = f"OpenRouter API 错误: {response.status_code} - {response.text}"
                print(f"❌ [调试] {error_msg}")
                print("🔍 [调试] 响应详情:")
                try:
                    error_data = response.json()
                    print(f"    错误类型: {error_data.get('error', {}).get('type', 'Unknown')}")
                    print(f"    错误消息: {error_data.get('error', {}).get('message', 'Unknown')}")
                    print(f"    错误代码: {error_data.get('error', {}).get('code', 'Unknown')}")
                except:
                    print(f"    原始响应: {response.text}")
                print("=" * 100)
                raise Exception(error_msg)
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            print(f"💥 [调试] OpenRouter API 调用失败: {error_msg}")
            print(f"    响应时间: {response_time}ms")
            print("=" * 100)
            
            return None, {
                "template_id": None,
                "template_name": "调用失败",
                "response_time_ms": response_time,
                "token_count": 0,
                "success": False,
                "error_message": error_msg,
                "divination_type": divination_type,
                "language": language
            }
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            payload = {
                "model": "openai/gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, this is a test message. Please respond with 'API connection successful!'"
                    }
                ],
                "max_tokens": 50
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return "successful" in content.lower()
            else:
                print(f"API连接测试失败: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            print(f"API连接测试失败: {e}")
            return False


# 全局服务实例
openrouter_service = OpenRouterService() 