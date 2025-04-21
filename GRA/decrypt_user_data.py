import sys
from pymongo import MongoClient
from aes_utils import aes_decrypt
import base64

# MongoDB连接配置
MONGO_URI = "mongodb://localhost:27017/"
USER_DB_NAME = "user"

def decrypt_user_data(username):
    # 连接MongoDB
    client = MongoClient(MONGO_URI)
    user_db = client[USER_DB_NAME]
    
    # 检查用户是否存在
    if username not in user_db.list_collection_names():
        print(f"用户 {username} 不存在")
        return
    
    # 获取用户数据
    user_collection = user_db[username]
    user_data = user_collection.find_one()
    
    if not user_data:
        print(f"用户 {username} 数据为空")
        return
    
    # 获取密钥
    key_data = user_data['data'].get('key_data', {})
    key_128 = base64.b64decode(key_data.get('key_128', '')) if key_data else None
    key_256 = base64.b64decode(key_data.get('key_256', '')) if key_data else None
    
    # 解密数据
    decrypted_data = {}
    for field, value in user_data['data'].items():
        if field in ['key_data', 'password', 'level_data', 'tag_data']:
            continue
            
        level = user_data['data'].get('level_data', {}).get('levels', {}).get(field, 1)
        if level == 1:
            decrypted_data[field] = value  # L1 级别数据直接显示明文
        elif level == 2:
            decrypted_data[field] = aes_decrypt(value, 128)  # L2 级别数据使用 128 位密钥解密
        elif level == 3:
            decrypted_data[field] = aes_decrypt(value, 256)  # L3 级别数据使用 256 位密钥解密
        else:
            decrypted_data[field] = value  # 未知等级显示密文
    
    # 输出解密后的数据
    print(f"用户 {username} 的解密数据：")
    for field, value in decrypted_data.items():
        print(f"{field}: {value}")
    
    client.close()

if __name__ == '__main__':
    username = sys.argv[1] if len(sys.argv) > 1 else input("请输入用户名：")
    decrypt_user_data(username)