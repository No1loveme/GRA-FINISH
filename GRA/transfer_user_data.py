from pymongo import MongoClient
import hashlib

# MongoDB连接配置
MONGO_URI = "mongodb://localhost:27017/"
USER_DB_NAME = "user"
USER_DATA_DB_NAME = "user_data"

def transfer_user_data():
    # 连接MongoDB
    client = MongoClient(MONGO_URI)
    user_db = client[USER_DB_NAME]
    user_data_db = client[USER_DATA_DB_NAME]
    collection = user_data_db["user_info"]
    key_collection = user_data_db["user_keys"]
    level_collection = user_data_db["user_levels"]
    tag_collection = user_data_db["user_tags"]

    # 遍历所有用户数据
    for user in collection.find():
        name = user['data']['名字']
        user_id = user['_id']
        user_collection = user_db[name]

        # 检查是否已存在相同ID的记录
        if user_collection.find_one({'_id': user_id}) is None:
            # 获取key、level和tag数据
            key_data = key_collection.find_one({'_id': user_id})
            level_data = level_collection.find_one({'_id': user_id})
            tag_data = tag_collection.find_one({'_id': user_id})

            # 将key、level和tag数据合并到用户数据中
            if key_data:
                user['data']['key_data'] = key_data
            if level_data:
                user['data']['level_data'] = level_data
            if tag_data:
                user['data']['tag_data'] = tag_data

            # 新增密码字段，初始为123456
            user['data']['password'] = hashlib.sha256("123456".encode()).hexdigest()

            # 将用户数据存储到以名字命名的表中
            user_collection.insert_one(user)

    client.close()

# 使用示例
if __name__ == '__main__':
    transfer_user_data()