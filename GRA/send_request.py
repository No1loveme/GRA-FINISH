from pymongo import MongoClient
from datetime import datetime
from Crypto.PublicKey import RSA
import uuid

# MongoDB连接配置
MONGO_URI = "mongodb://localhost:27017/"
USER_DB_NAME = "user"
REQUEST_DB_NAME = "request"

def generate_and_store_keys(username):
    """
    为用户生成并存储RSA密钥对
    :param username: 用户名
    :return: 公钥字符串
    """
    client = MongoClient(MONGO_URI)
    user_db = client[USER_DB_NAME]
    
    # 生成RSA密钥对
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    
    # 只更新密钥部分，不影响其他数据
    user_collection = user_db[username]
    user_collection.update_one(
        {},
        {'$set': {
            'data.private_key': private_key.decode(),
            'data.public_key': public_key.decode()
        }},
        upsert=True
    )
    
    client.close()
    return public_key.decode()

def send_request(from_user, to_user):
    """
    发送请求
    :param from_user: 发送请求的用户
    :param to_user: 接收请求的用户
    """
    # 检查是否尝试向自己发送请求
    if from_user == to_user:
        print("不能向自己发送请求")
        return False

    # 连接MongoDB
    client = MongoClient(MONGO_URI)
    user_db = client[USER_DB_NAME]
    request_db = client[REQUEST_DB_NAME]
    
    # 检查发送用户的密钥是否存在，不存在则生成
    from_user_collection = user_db[from_user]
    from_user_data = from_user_collection.find_one()
    if not from_user_data or 'public_key' not in from_user_data.get('data', {}):
        public_key = generate_and_store_keys(from_user)
    else:
        public_key = from_user_data['data']['public_key']
    
    # 检查接收用户的user集合是否存在
    if to_user not in user_db.list_collection_names():
        print(f"用户 {to_user} 的user集合不存在")
        return False
    
    # 获取发送用户的公钥
    from_user_collection = user_db[from_user]
    from_user_data = from_user_collection.find_one()
    if not from_user_data or 'public_key' not in from_user_data['data']:
        print(f"用户 {from_user} 的公钥不存在")
        return False
    
    public_key = from_user_data['data']['public_key']
    
    # 创建请求记录
    request_record = {
        'request_id': str(uuid.uuid4())[:8],
        'from_user': from_user,
        'public_key': public_key,
        'status': 'pending',
        'timestamp': datetime.now()
    }
    
    # 插入请求记录
    to_user_collection = request_db[to_user]
    # 检查是否已存在来自该用户的请求
    existing_request = to_user_collection.find_one({'from_user': from_user})
    if existing_request:
        print(f"用户 {to_user} 已有来自 {from_user} 的请求")
        client.close()
        return False

    result = to_user_collection.insert_one(request_record)
    
    client.close()
    
    if result.inserted_id:
        print(f"请求已成功发送给用户 {to_user}")
        return True
    else:
        print("请求发送失败")
        return False

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("用法: python send_request.py <发送用户> <接收用户>")
    else:
        from_user = sys.argv[1]
        to_user = sys.argv[2]
        send_request(from_user, to_user)