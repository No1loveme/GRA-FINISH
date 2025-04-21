from pymongo import MongoClient
import xml.etree.ElementTree as ET
import hashlib
import base64  # 添加 base64 导入
from Crypto.Cipher import AES  # 添加 AES 导入
from aes_utils import aes_encrypt  # 从新文件中导入加密函数

# MongoDB连接配置
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "user_data"
COLLECTION_NAME = "user_info"

# AES加密函数
def aes_encrypt(data, key_size):
    key = b'This is a key128' if key_size == 128 else b'This is a key456This is a key456'
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

# 新增：读取XML文件函数
def read_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    return root

# 数据类型映射
DATA_TYPE_MAPPING = {
    '名字': ('VARCHAR', 2),
    '性别': ('VARCHAR', 2),
    '年龄': ('INT', 0),
    '身高': ('FLOAT', 1),
    '体重': ('FLOAT', 1)
}

def process_and_store_xml(file_path):
    # 连接MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # 新增：标签集合
    tag_collection = db["user_tags"]
    # 新增：密钥集合
    key_collection = db["user_keys"]
    # 新增：等级集合
    level_collection = db["user_levels"]
    # 新增：访问控制集合
    access_collection = db["access_control"]
    
    # 初始化访问控制表为空
    access_collection.delete_many({})
    
    # 使用新增的读取函数
    root = read_xml(file_path)
    
    for i, user in enumerate(root.findall('用户')):
        # 获取所有字段值
        name = user.find('名字').text
        gender = user.find('性别').text
        age = user.find('年龄').text
        height = user.find('身高').text
        weight = user.find('体重').text
        
        # 拼接所有字段并生成复杂ID
        combined_data = f"{name}{gender}{age}{height}{weight}"
        user_id = hashlib.sha256(combined_data.encode('utf-8')).hexdigest()
        
        # 检查是否已存在相同ID的记录
        if collection.find_one({'_id': user_id}) is not None:
            print(f"用户 {name} 已存在，跳过处理")
            continue
            
        user_data = {
            '_id': user_id,
            'data': {}
        }
        # 新增：标签数据
        tag_data = {
            '_id': user_id,
            'data_types': {}
        }
        
        # 初始化等级数据
        level_data = {
            '_id': user_id,
            'levels': {}
        }
        
        for child in user:
            field = child.tag
            value = child.text
            
            # 获取数据类型
            data_type, type_code = DATA_TYPE_MAPPING.get(field, ('VARCHAR', 2))
            
            # 分级处理
            if field == '名字':  # 第一级
                processed_value = value
                level = 1
            elif field in ['性别', '年龄']:  # 第二级
                processed_value = aes_encrypt(value, 128)  # 调用新文件中的加密函数
                level = 2
            else:  # 第三级
                processed_value = aes_encrypt(value, 256)  # 调用新文件中的加密函数
                level = 3
                
            # 存储数据
            user_data['data'][field] = processed_value
            # 存储标签
            tag_data['data_types'][field] = {
                'type': data_type,
                'type_code': type_code
            }
            # 存储等级
            level_data['levels'][field] = level
        
        # 插入MongoDB
        collection.update_one({'_id': user_id}, {'$set': user_data}, upsert=True)
        # 插入标签表
        tag_collection.update_one({'_id': user_id}, {'$set': tag_data}, upsert=True)
        # 插入等级表
        level_collection.update_one({'_id': user_id}, {'$set': level_data}, upsert=True)
        
        # 生成并存储密钥
        key_128 = b'This is a key123'
        key_256 = b'This is a key456This is a key456'
        key_data = {
            '_id': user_id,
            'key_128': base64.b64encode(key_128).decode(),
            'key_256': base64.b64encode(key_256).decode()
        }
        key_collection.update_one({'_id': user_id}, {'$set': key_data}, upsert=True)
    
    client.close()

# 使用示例
if __name__ == '__main__':
    process_and_store_xml('f:\\GRA\\data.xml')