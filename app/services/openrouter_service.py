import requests
import json
from typing import Optional
from ..config import settings
from sqlalchemy.orm import Session
from ..models import PromptTemplate, PromptUsageHistory


class OpenRouterService:
    """OpenRouter API 服务类"""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "FateWave",
            "Content-Type": "application/json"
        }
    
    def get_prompt_from_db(self, db: Session, divination_type: str = "tarot", language: str = "en"):
        """从数据库获取提示词模板"""
        # 首先尝试获取指定类型的提示词
        prompt_template = db.query(PromptTemplate).filter(
            PromptTemplate.divination_type == divination_type,
            PromptTemplate.language == language,
            PromptTemplate.is_active == True
        ).order_by(PromptTemplate.is_default.desc()).first()
        
        if not prompt_template:
            # 如果没找到，尝试获取通用类型
            prompt_template = db.query(PromptTemplate).filter(
                PromptTemplate.divination_type == "general",
                PromptTemplate.language == language,
                PromptTemplate.is_active == True
            ).first()
        
        if not prompt_template:
            # 如果还是没找到，返回硬编码的备用提示词
            print(f"⚠️ 数据库中未找到提示词模板 (type: {divination_type}, lang: {language})，使用备用提示词")
            return self.get_fallback_prompts(language)
        
        print(f"✅ 使用数据库提示词模板: {prompt_template.name}")
        
        return {
            "system": prompt_template.system_prompt,
            "user_template": prompt_template.user_template,
            "template_id": prompt_template.id,
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
            # 从数据库获取提示词
            prompts = self.get_prompt_from_db(db, divination_type, language)
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": prompts["system"]
                    },
                    {
                        "role": "user", 
                        "content": prompts["user_template"].format(question=question)
                    }
                ],
                "temperature": prompts["temperature"],
                "max_tokens": prompts["max_tokens"]
            }
            
            # 打印调试信息
            print(f"发送到OpenRouter的请求头: {self.headers}")
            print(f"使用的模型: {model}")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            print(f"OpenRouter响应状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"OpenRouter错误响应: {response.text}")
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                
                return answer, {
                    "template_id": prompts["template_id"],
                    "response_time_ms": response_time,
                    "token_count": result.get("usage", {}).get("total_tokens", 0),
                    "success": True,
                    "actual_system_prompt": prompts["system"],
                    "actual_user_prompt": prompts["user_template"].format(question=question)
                }
            else:
                error_msg = f"OpenRouter API 错误: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            print(f"OpenRouter API 调用失败: {error_msg}")
            
            return None, {
                "template_id": None,
                "response_time_ms": response_time,
                "token_count": 0,
                "success": False,
                "error_message": error_msg
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