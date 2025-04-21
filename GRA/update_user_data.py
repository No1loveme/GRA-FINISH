from pymongo import MongoClient
from aes_utils import aes_encrypt
import hashlib

# MongoDB连接配置
MONGO_URI = "mongodb://localhost:27017/"
USER_DB_NAME = "user"

def update_user_data(username, field, new_value, security_level):
    # 连接MongoDB
    client = MongoClient(MONGO_URI)
    user_db = client[USER_DB_NAME]
    
    # 检查用户是否存在
    if username not in user_db.list_collection_names():
        print(f"用户 {username} 不存在")
        return False
    
    # 获取用户集合
    user_collection = user_db[username]
    user_data = user_collection.find_one()
    
    if not user_data:
        print(f"用户 {username} 数据为空")
        return False
    
    # 根据安全等级进行加密处理
    if security_level == 1:
        processed_value = new_value  # L1 级别数据不加密
    elif security_level == 2:
        processed_value = aes_encrypt(new_value, 128)  # L2 级别数据使用 128 位密钥加密
    elif security_level == 3:
        processed_value = aes_encrypt(new_value, 256)  # L3 级别数据使用 256 位密钥加密
    else:
        print("无效的安全等级")
        return False
    
    # 更新数据
    update_result = user_collection.update_one(
        {'_id': user_data['_id']},
        {
            '$set': {
                f'data.{field}': processed_value,
                f'data.level_data.levels.{field}': security_level
            }
        }
    )
    
    client.close()
    
    if update_result.modified_count > 0:
        print(f"用户 {username} 的 {field} 字段更新成功")
        return True
    else:
        print("更新失败")
        return False

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 5:
        print("用法: python update_user_data.py <用户名> <字段名> <新值> <安全等级>")
    else:
        username = sys.argv[1]
        field = sys.argv[2]
        new_value = sys.argv[3]
        security_level = int(sys.argv[4])
        update_user_data(username, field, new_value, security_level)