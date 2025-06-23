#!/usr/bin/env python3
"""
FastAPI 后端测试脚本
用于测试各个API接口是否正常工作
"""

import requests
import json
import time


BASE_URL = "http://localhost:8000"


def test_health_check():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查错误: {e}")
        return False


def test_create_session():
    """测试创建会话接口"""
    print("\n🆔 测试创建会话接口...")
    try:
        response = requests.post(f"{BASE_URL}/api/divination/session")
        if response.status_code == 200:
            data = response.json()
            session_id = data["data"]["session_id"]
            print("✅ 会话创建成功")
            print(f"   会话ID: {session_id}")
            return session_id
        else:
            print(f"❌ 会话创建失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 会话创建错误: {e}")
        return None


def test_divination(session_id):
    """测试占卜接口"""
    print("\n🔮 测试占卜接口...")
    try:
        payload = {
            "question": "我今天的运势如何？",
            "language": "zh-CN",
            "session_id": session_id
        }
        
        print(f"   发送请求: {json.dumps(payload, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/divination",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 占卜请求成功")
            print(f"   占卜ID: {data['data']['id']}")
            print(f"   问题: {data['data']['question']}")
            print(f"   答案预览: {data['data']['answer'][:100]}...")
            return True
        else:
            print(f"❌ 占卜请求失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 占卜请求错误: {e}")
        return False


def test_usage_stats(session_id):
    """测试使用统计接口"""
    print("\n📊 测试使用统计接口...")
    try:
        response = requests.get(f"{BASE_URL}/api/divination/usage?session_id={session_id}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 使用统计获取成功")
            print(f"   统计数据: {data['data']}")
            return True
        else:
            print(f"❌ 使用统计获取失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 使用统计错误: {e}")
        return False


def test_history(session_id):
    """测试历史记录接口"""
    print("\n📚 测试历史记录接口...")
    try:
        response = requests.get(f"{BASE_URL}/api/divination/history?session_id={session_id}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 历史记录获取成功")
            print(f"   记录数量: {len(data['data']['divinations'])}")
            print(f"   总计: {data['data']['total']}")
            return True
        else:
            print(f"❌ 历史记录获取失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 历史记录错误: {e}")
        return False


def main():
    """主测试流程"""
    print("🚀 开始 FateWave API 测试")
    print("=" * 50)
    
    # 1. 健康检查
    if not test_health_check():
        print("\n💥 服务器未启动或不可用，请检查后端服务")
        return
    
    # 2. 创建会话
    session_id = test_create_session()
    if not session_id:
        print("\n💥 会话创建失败，无法继续测试")
        return
    
    # 3. 测试占卜功能
    if not test_divination(session_id):
        print("\n💥 占卜功能测试失败")
        return
    
    # 等待一秒，确保数据已保存
    time.sleep(1)
    
    # 4. 测试使用统计
    if not test_usage_stats(session_id):
        print("\n⚠️  使用统计功能有问题")
    
    # 5. 测试历史记录
    if not test_history(session_id):
        print("\n⚠️  历史记录功能有问题")
    
    print("\n" + "=" * 50)
    print("🎉 API 测试完成！")
    print("\n💡 提示:")
    print(f"   - 访问 {BASE_URL}/docs 查看完整API文档")
    print(f"   - 访问 {BASE_URL}/health 检查服务状态")
    print(f"   - 会话ID: {session_id}")


if __name__ == "__main__":
    main() 