from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import hashlib
import subprocess
import json  # Add this import
from flask import jsonify
from Crypto.PublicKey import RSA
from handle_request import handle_request

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB连接配置
MONGO_URI = "mongodb://localhost:27017/"
USER_DB_NAME = "user"
USER_DATA_DB_NAME = "user_data"
REQUEST_DB_NAME = "request"
PERMISSION_DB_NAME = "permission"  # 确保这行存在

@app.route('/')
def index():
    if 'username' in session:
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # 管理员登录
    if username == 'admin':
        if hashlib.sha256(password.encode()).hexdigest() == hashlib.sha256("123456".encode()).hexdigest():
            session['username'] = 'admin'
            return redirect('/dashboard')
        else:
            return "密码错误"
    
    client = MongoClient(MONGO_URI)
    user_db = client[USER_DB_NAME]
    
    if username not in user_db.list_collection_names():
        return "用户名不存在"
        
    user_collection = user_db[username]
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user = user_collection.find_one({'data.password': hashed_password})
    
    if user:
        session['username'] = username
        return redirect('/dashboard')
    else:
        return "密码错误"

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect('/')
        
    client = MongoClient(MONGO_URI)
    user_db = client[USER_DB_NAME]
    request_db = client[REQUEST_DB_NAME]
    permission_db = client[PERMISSION_DB_NAME]  # 添加这行初始化permission_db
    
    # 管理员查看所有用户
    if session['username'] == 'admin':
        users = []
        for collection_name in user_db.list_collection_names():
            user_collection = user_db[collection_name]
            user = user_collection.find_one()
            if user:
                users.append({
                    'name': collection_name,
                    'id': user['_id']
                })
        return render_template('dashboard.html', is_admin=True, users=users)
    
    # 普通用户查看自己的数据
    user_collection = user_db[session['username']]
    user_data = user_collection.find_one()
    
    # 获取用户名字
    user_name = user_data['data'].get('名字', '')
    
    # 整合用户数据
    unified_data = {
        '名字': {
            '值': user_data['data'].get('名字', ''),
            '类型': user_data['data'].get('tag_data', {}).get('data_types', {}).get('名字', {}).get('type_code', ''),
            '等级': user_data['data'].get('level_data', {}).get('levels', {}).get('名字', '')
        },
        '性别': {
            '值': user_data['data'].get('性别', ''),
            '类型': user_data['data'].get('tag_data', {}).get('data_types', {}).get('性别', {}).get('type_code', ''),
            '等级': user_data['data'].get('level_data', {}).get('levels', {}).get('性别', '')
        },
        '年龄': {
            '值': user_data['data'].get('年龄', ''),
            '类型': user_data['data'].get('tag_data', {}).get('data_types', {}).get('年龄', {}).get('type_code', ''),
            '等级': user_data['data'].get('level_data', {}).get('levels', {}).get('年龄', '')
        },
        '身高': {
            '值': user_data['data'].get('身高', ''),
            '类型': user_data['data'].get('tag_data', {}).get('data_types', {}).get('身高', {}).get('type_code', ''),
            '等级': user_data['data'].get('level_data', {}).get('levels', {}).get('身高', '')
        },
        '体重': {
            '值': user_data['data'].get('体重', ''),
            '类型': user_data['data'].get('tag_data', {}).get('data_types', {}).get('体重', {}).get('type_code', ''),
            '等级': user_data['data'].get('level_data', {}).get('levels', {}).get('体重', '')
        },
        'key_data': {k: v for k, v in user_data['data'].get('key_data', {}).items() if k != '_id'},
        'password': user_data['data'].get('password', '')
    }
    
    # 处理解密请求
    decrypted_data = None
    if request.method == 'POST' and 'decrypt' in request.form:
        # 调用 decrypt_user_data.py 进行解密
        result = subprocess.run(['python', 'f:\\GRA\\decrypt_user_data.py', session['username']], capture_output=True, text=True)
        if result.returncode == 0:
            # 过滤掉RSA密钥相关数据
            decrypted_data = {}
            for line in result.stdout.splitlines():
                if ':' in line and not any(keyword in line for keyword in ['public_key', 'private_key', 'key_data']):
                    key, value = line.split(':', 1)  # 只分割第一个冒号
                    decrypted_data[key.strip()] = value.strip()
        else:
            decrypted_data = "解密失败"
    
    # 获取当前用户的请求数据
    requests = []
    if session['username'] in request_db.list_collection_names():
        requests = list(request_db[session['username']].find().sort('timestamp', -1))
    
    # 获取权限数据
    permissions = []
    if session['username'] in permission_db.list_collection_names():
        permissions = list(permission_db[session['username']].find().sort('timestamp', -1))
    
    client.close()
    return render_template('dashboard.html', 
                         is_admin=False, 
                         user_data=unified_data, 
                         user_name=user_name, 
                         decrypted_data=decrypted_data,
                         requests=requests,
                         permissions=permissions)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/delete_user', methods=['POST'])
def delete_user():
    if 'username' not in session or session['username'] != 'admin':
        return redirect('/')
    
    username = request.form['username']
    client = MongoClient(MONGO_URI)
    user_db = client[USER_DB_NAME]
    
    if username in user_db.list_collection_names():
        user_db.drop_collection(username)
    
    client.close()
    return redirect('/dashboard')

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'username' not in session or session['username'] != 'admin':
        return redirect('/')
    
    username = request.form['username']
    password = request.form['password']
    
    # 生成RSA密钥对
    key = RSA.generate(2048)
    public_key = key.publickey().export_key().decode('utf-8')
    private_key = key.export_key().decode('utf-8')
    
    client = MongoClient(MONGO_URI)
    user_db = client[USER_DB_NAME]
    
    if username not in user_db.list_collection_names():
        user_collection = user_db[username]
        user_collection.insert_one({
            'data': {
                '名字': username,
                'password': hashlib.sha256(password.encode()).hexdigest(),
                'public_key': public_key,
                'private_key': private_key  # 注意：实际应用中应更安全地存储私钥
            }
        })
        client.close()
        return redirect('/dashboard')
    else:
        client.close()
        return "用户名已存在"

@app.route('/update_users', methods=['POST'])
def update_users():
    if 'username' not in session or session['username'] != 'admin':
        return redirect('/')
    
    try:
        # 首先更新user_data库
        import subprocess
        subprocess.run(['python', 'f:\\GRA\\process_to_mongodb.py'], check=True)
        
        # 然后更新user库
        client = MongoClient(MONGO_URI)
        user_db = client[USER_DB_NAME]
        user_data_db = client[USER_DATA_DB_NAME]
        
        # 获取所有现有用户集合
        existing_collections = user_db.list_collection_names()
        
        # 遍历user_data库中的用户信息
        for user in user_data_db["user_info"].find():
            name = user['data']['名字']
            user_id = user['_id']
            
            # 如果用户集合不存在，则创建
            if name not in existing_collections:
                user_db.create_collection(name)
            
            user_collection = user_db[name]
            
            # 检查是否已存在相同ID的记录
            if user_collection.find_one({'_id': user_id}) is None:
                # 获取key、level和tag数据
                key_data = user_data_db["user_keys"].find_one({'_id': user_id})
                level_data = user_data_db["user_levels"].find_one({'_id': user_id})
                tag_data = user_data_db["user_tags"].find_one({'_id': user_id})
                
                # 合并数据
                user['data']['key_data'] = key_data
                user['data']['level_data'] = level_data
                user['data']['tag_data'] = tag_data
                
                # 设置默认密码
                user['data']['password'] = hashlib.sha256("123456".encode()).hexdigest()
                
                # 插入新用户
                user_collection.insert_one(user)
        
        client.close()
        return redirect('/dashboard')
    except Exception as e:
        return f"更新失败: {str(e)}"

@app.route('/update_data', methods=['POST'])
def update_data():
    if 'username' not in session:
        return jsonify({'success': False})
    
    data = request.get_json()
    field = data['field']
    new_value = data['newValue']
    security_level = data['securityLevel']
    
    # 数据类型验证
    if field in ['年龄', '身高', '体重']:
        try:
            float(new_value)  # 尝试转换为数字
        except ValueError:
            return jsonify({'success': False, 'message': '无效的数字格式'})
    
    # 调用update_user_data.py
    result = subprocess.run(
        ['python', 'update_user_data.py', session['username'], field, new_value, security_level],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': result.stderr})


@app.route('/handle_request', methods=['POST'])
def handle_request_route():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    data = request.get_json()
    result = handle_request(session['username'], data['from_user'], data['action'])
    return jsonify({'success': result})


@app.route('/delete_permission', methods=['POST'])
def delete_permission():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    data = request.get_json()
    from_user = data['from_user']
    
    client = MongoClient(MONGO_URI)
    permission_db = client[PERMISSION_DB_NAME]
    
    # 删除权限记录
    result = permission_db[session['username']].delete_one({'from_user': from_user})
    
    client.close()
    
    if result.deleted_count > 0:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '未找到权限记录'})

@app.route('/query')
def query():
    if 'username' not in session:
        return redirect('/')
    return render_template('query.html')


@app.route('/send_request', methods=['POST'])
def send_request_route():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    data = request.get_json()
    receiver = data['receiver']
    
    # 调用send_request.py
    result = subprocess.run(
        ['python', 'send_request.py', session['username'], receiver],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': result.stderr})

@app.route('/query_data', methods=['POST'])
def query_data_route():
    if 'username' not in session:
        return "未登录", 401
    
    data = request.get_json()
    target_user = data['target_user']
    
    try:
        # 获取当前脚本路径
        import os
        script_path = os.path.join(os.path.dirname(__file__), 'query_data.py')
        
        # 调用query_data.py
        result = subprocess.run(
            ['python', script_path, session['username'], target_user],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode == 0:
            return result.stdout  # 直接返回原始输出
        else:
            return f"查询失败: {result.stderr}", 400
            
    except Exception as e:
        return f"查询异常: {str(e)}", 500


if __name__ == '__main__':
    app.run(debug=True)