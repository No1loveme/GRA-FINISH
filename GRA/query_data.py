from pymongo import MongoClient
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from aes_utils import aes_decrypt
import base64
import json

# MongoDB连接配置
MONGO_URI = "mongodb://localhost:27017/"
USER_DB_NAME = "user"
PERMISSION_DB_NAME = "permission"

def query_data(query_user, target_user):
    """查询用户数据
    :param query_user: 查询用户
    :param target_user: 目标用户
    :return: 返回包含RSA解密后数据的JSON
    """
    client = MongoClient(MONGO_URI)
    try:
        user_db = client[USER_DB_NAME]
        permission_db = client[PERMISSION_DB_NAME]
        
        # 检查目标用户是否存在
        if target_user not in user_db.list_collection_names():
            print(f"用户 {target_user} 不存在")
            client.close()
            return False
        
        # 检查查询权限
        permission_collection = permission_db[target_user]
        permission_data = permission_collection.find_one({'from_user': query_user})
        if not permission_data:
            print(f"用户 {query_user} 没有权限查询用户 {target_user} 的数据")
            client.close()
            return False
        
        # 获取目标用户数据
        target_collection = user_db[target_user]
        target_data = target_collection.find_one()
        if not target_data:
            print(f"用户 {target_user} 数据为空")
            client.close()
            return False
        
        # 解密目标用户的等级1和2数据
        decrypted_data = {}
        for field, value in target_data['data'].items():
            if field in ['key_data', 'password', 'level_data', 'tag_data']:
                continue
                
            level = target_data['data'].get('level_data', {}).get('levels', {}).get(field, 1)
            if level == 1:
                decrypted_data[field] = value  # 等级1数据直接使用原始值
            elif level == 2:
                decrypted_data[field] = aes_decrypt(value, 128)  # 仅解密等级2数据
        
        # 使用查询用户的公钥加密数据
        query_collection = user_db[query_user]
        query_data = query_collection.find_one()
        if not query_data or 'public_key' not in query_data['data']:
            print(f"用户 {query_user} 的公钥不存在")
            client.close()
            return False
        
        public_key = RSA.import_key(query_data['data']['public_key'])
        cipher = PKCS1_OAEP.new(public_key)
        
        encrypted_data = {}
        for field, value in decrypted_data.items():
            try:
                max_length = 214
                value_str = str(value)
                if len(value_str.encode()) > max_length:
                    value_str = value_str[:max_length//4]
                encrypted_data[field] = base64.b64encode(cipher.encrypt(value_str.encode())).decode()
            except Exception as e:
                print(f"加密 {field} 时出错: {str(e)}")
                encrypted_data[field] = "加密失败"
        
        # 输出加密后的数据
        print(f"用户 {target_user} 的加密数据：")
        for field, value in encrypted_data.items():
            print(f"{field}: {value}")
        
        # 使用查询用户的私钥解密数据
        if not query_data or 'private_key' not in query_data['data']:
            print(f"用户 {query_user} 的私钥不存在")
            client.close()
            return False
        
        private_key = RSA.import_key(query_data['data']['private_key'])
        cipher = PKCS1_OAEP.new(private_key)
        
        final_result = {}
        for field, value in encrypted_data.items():
            try:
                decrypted_bytes = cipher.decrypt(base64.b64decode(value))
                final_result[field] = decrypted_bytes.decode()
            except Exception as e:
                print(f"解密 {field} 时出错: {str(e)}")
                final_result[field] = "解密失败"
        
        # 返回解密后的最终结果
        return json.dumps({
            'success': True,
            'data': final_result,
            'message': '查询成功'
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({'success': False, 'message': f'查询过程中出错: {str(e)}'})
    finally:
        client.close()

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("用法: python query_data.py <查询用户> <目标用户>")
    else:
        result = query_data(sys.argv[1], sys.argv[2])
        print(result)