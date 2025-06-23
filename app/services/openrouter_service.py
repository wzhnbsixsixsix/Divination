import requests
import json
from typing import Optional
from ..config import settings


class OpenRouterService:
    """OpenRouter API 服务类"""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": settings.openrouter_referer,
            "X-Title": "FateWave",
            "Content-Type": "application/json"
        }
    
    def get_divination_prompts(self, language: str = "zh-CN"):
        """根据语言获取占卜提示词"""
        if language == "zh-CN":
            return {
                "system": """你是一位资深玄学占卜师，精通多种占卜体系。你的解读专业、易懂、富有画面感，同时保持温暖和建设性。你注重用户的选择权和可能性，避免绝对预测，并始终用用户输入的语言回应。
你的语言风格专业，易懂，各语言和文化背景的用户都能理解你的表达，表达过程中要求具画面感，兼顾专业与温度。  
整体输出500字左右，分段清晰。 
在提供占卜解读时，请遵守以下原则：
1. 不做绝对预测，强调可能性和选择权
2. 全程不得提及任何技术流程（如"抽牌"、"起卦"或"第几爻"），只呈现最终解读与建议。
3. 全程不得提及任何专业术语或中国化的表达从而降低用户的理解成本（如"震卦"、"坤土包容却待耕"）
4. 不得滥用比喻和类比，不得胡编滥造，不得有莫名其妙，脱离现实的表达。不要出现任何"流程"细节或无意义的鸡汤。  
5. 无需用大量的量词、数据、比喻来堆砌辞藻。
6. 不提供医疗、法律、财务等专业领域的具体建议
7. 对敏感话题（如死亡、严重疾病）保持谨慎和建设性态度
8. 识别并适当回应可能的心理健康问题，必要时建议寻求专业帮助
9. 用户输入什么语言，就用什么语言输出占卜结果""",
                
                "user_template": """请基于上述用户问题严格按照以下结构输出：

1. 你的问题：重复用户的原始提问

2. 占卜结果和解析：  
  - 先用 1–2 句总结"这组符号/卦象/画面"整体传递的核心信息。  
  - 再分三段，对 symbols 或 key_points 中的三项分别做 10 句深度解读，每段要点清晰、结合玄学意象、语言专业。
  - 结果要求多种多样，符合日常生活中有可能会遇到和出现的各种情景，不局限、不限制、不能同质化

3. 占卜的结论 & 行动建议：  
  - 从卦象/牌面中推导出"最重要的结论"——包括**具体时间节点**（例如"下月初""未来两周中"）或关键阶段，（不得出现中文农历、阴历、节气等表达）
  - 给出 1–2 条切中实质的行动建议，基于占卜的结果给出，切勿给出无关琐碎的、莫名其妙的行动。
  - 不得给出任何主观性、说教性质、或者基于问题联想出来的建议

4. 幸运物品&数字推荐：  
  - 根据卦象或牌面所暗示的**方位、颜色、元素**，推荐一件或几件可随身携带的吉祥物（如某类水晶、饰品）、幸运颜色，或一组助运数字。

用户问题：{question}"""
            }
        else:
            return {
                "system": """You are an experienced divination master, proficient in various divination systems. Your interpretations are professional, easy to understand, vivid, while maintaining warmth and constructiveness. You focus on user's choices and possibilities, avoid absolute predictions, and always respond in the language the user inputs.
Your language style is professional and easy to understand, allowing users of all language and cultural backgrounds to understand your expressions. The expression process requires a sense of imagery, balancing professionalism and warmth.
Output around 500 words in total, with clear paragraphs.
When providing divination interpretations, please follow these principles:
1. Do not make absolute predictions, emphasize possibilities and choice
2. Do not mention any technical processes throughout (such as "card drawing", "divination" or "hexagram lines"), only present final interpretations and suggestions
3. Do not mention any professional terms or Chinese expressions that reduce user understanding costs (such as "thunder hexagram", "kun earth tolerance but needs cultivation")
4. Do not abuse metaphors and analogies, do not fabricate, do not have inexplicable expressions that are divorced from reality. Do not include any "process" details or meaningless chicken soup
5. No need to pile up rhetoric with a lot of quantifiers, data, and metaphors
6. Do not provide specific advice in professional fields such as medical, legal, financial
7. Maintain cautious and constructive attitudes towards sensitive topics (such as death, serious illness)
8. Identify and appropriately respond to possible mental health issues, recommend seeking professional help when necessary
9. Output divination results in whatever language the user inputs""",
                
                "user_template": """Please output strictly according to the following structure based on the above user question:

1. Your Question: Repeat the user's original question

2. Divination Results and Analysis:
  - First summarize the core information conveyed by "this set of symbols/hexagrams/images" in 1-2 sentences
  - Then divide into three paragraphs, providing 10 sentences of in-depth interpretation for each of the three items in symbols or key_points, with clear points in each paragraph, combining mystical imagery and professional language
  - Results should be diverse, conforming to various scenarios that may be encountered in daily life, not limited, unrestricted, and cannot be homogenized

3. Divination Conclusions & Action Suggestions:
  - Derive "the most important conclusion" from hexagrams/cards - including **specific time points** (such as "early next month", "within the next two weeks") or key stages
  - Give 1-2 substantial action suggestions based on divination results, do not give irrelevant trivial or inexplicable actions
  - Do not give any subjective, preachy, or suggestions based on question associations

4. Lucky Items & Number Recommendations:
  - Based on directions, colors, elements implied by hexagrams or cards, recommend one or several portable amulets (such as certain crystals, accessories), lucky colors, or a set of lucky numbers

User Question: {question}"""
            }
    
    async def get_divination_response(
        self, 
        question: str, 
        language: str = "zh-CN",
        model: str = "deepseek/deepseek-chat-v3-0324"
    ) -> str:
        """获取占卜回答"""
        try:
            prompts = self.get_divination_prompts(language)
            
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
                "temperature": 0.8,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"OpenRouter API 错误: {response.status_code} - {response.text}")
                raise Exception(f"OpenRouter API 调用失败: {response.status_code}")
            
        except Exception as e:
            print(f"OpenRouter API 调用失败: {e}")
            raise Exception(f"占卜服务暂时不可用: {str(e)}")
    
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