from pymongo import MongoClient

# MongoDB连接配置
MONGO_URI = "mongodb://localhost:27017/"
USER_DB_NAME = "user"
PERMISSION_DB_NAME = "permission"

def create_permission_db():
    # 连接MongoDB
    client = MongoClient(MONGO_URI)
    
    # 获取user库中的所有用户名
    user_db = client[USER_DB_NAME]
    usernames = user_db.list_collection_names()
    
    # 创建permission库
    permission_db = client[PERMISSION_DB_NAME]
    
    # 为每个用户创建一个集合
    for username in usernames:
        if username not in permission_db.list_collection_names():
            permission_db.create_collection(username)
            print(f"为用户 {username} 创建了权限集合")
        else:
            print(f"用户 {username} 的权限集合已存在")
    
    client.close()

if __name__ == '__main__':
    create_permission_db()