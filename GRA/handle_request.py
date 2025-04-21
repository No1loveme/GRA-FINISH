from pymongo import MongoClient

# MongoDB连接配置
MONGO_URI = "mongodb://localhost:27017/"
REQUEST_DB_NAME = "request"
PERMISSION_DB_NAME = "permission"

def handle_request(username, from_user, action):
    """处理请求
    :param username: 当前用户
    :param from_user: 发送请求的用户
    :param action: 操作（approve/reject）
    """
    client = MongoClient(MONGO_URI)
    request_db = client[REQUEST_DB_NAME]
    permission_db = client[PERMISSION_DB_NAME]
    
    # 获取请求
    user_collection = request_db[username]
    request_data = user_collection.find_one({'from_user': from_user})
    if not request_data:
        print(f"来自 {from_user} 的请求不存在")
        client.close()
        return False
    
    # 处理请求
    if action == 'approve':
        # 将用户名和公钥写入permission库
        permission_collection = permission_db[username]
        permission_collection.insert_one({
            'from_user': request_data['from_user'],
            'public_key': request_data['public_key']
        })
        print(f"已同意来自 {request_data['from_user']} 的请求")
    
    # 删除请求
    user_collection.delete_one({'from_user': from_user})
    print(f"已删除来自 {from_user} 的请求")
    
    client.close()
    return True

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 4:
        print("用法: python handle_request.py <用户名> <发送请求的用户> <操作>")
    else:
        username = sys.argv[1]
        from_user = sys.argv[2]
        action = sys.argv[3]
        handle_request(username, from_user, action)