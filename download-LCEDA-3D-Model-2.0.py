import requests
import json
import codecs
import re

# --- 配置信息 ---
DEFAULT_PATH = '0819f05c4eef4c71ace90d822a990e87'

def show_welcome():
    print("=" * 50)
    print("   欢迎使用立创 EDA 3D 模型下载工具")
    print("   代码原作者：kulya97")
    print("   修改&打包：薛定谔的小兔纸")
    print("=" * 50)
    print()

def sanitize_filename(name):
    # 1. 将 Windows 非法字符替换为下划线: \ / : * ? " < > |
    # 2. 将 空格 和 减号 也替换为下划线
    # [\\/:*?"<>| \-] 
    # \\/ : * ? " < > | 是非法字符
    # \s 代表空格，\- 代表减号
    return re.sub(r'[\\/:*?"<>|\s]', '_', name)

def download_lceda_model():
    show_welcome()
    
    code = input("请输入元器件编号 (例如 C8734): ").strip().upper()
    if not code:
        print("错误：编号不能为空！")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://pro.lceda.cn/',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        # 1. 搜索 Device ID
        print(f"\n[1/4] 正在搜索器件: {code}...")
        has_url = 'https://pro.lceda.cn/api/eda/product/search'
        has_formdata = {
            'keyword': code,
            'needAggs': 'true',
            'url': '/api/eda/product/list',
            'currPage': '1',
            'pageSize': '10'
        }
        r0 = requests.post(has_url, data=has_formdata, headers=headers, timeout=10)
        
        if r0.status_code == 418:
            print("❌ 错误：触发了服务器反爬虫机制 (418)。请稍后再试。")
            return

        json_data = r0.json()
        product_list = json_data.get('result', {}).get('productList', [])
        
        if not product_list:
            print(f"❌ 未找到编号为 {code} 的产品。")
            return

        has_device = product_list[0]['hasDevice']

        # 2. 获取详情
        print(f"[2/4] 获取详情中...")
        url = 'https://pro.lceda.cn/api/devices/searchByIds'
        r1 = requests.post(url, data={'uuids[]': has_device, 'path': DEFAULT_PATH}, headers=headers)
        result1 = r1.json().get('result', [{}])[0]
        attributes = result1.get('attributes', {})
        
        model_id = attributes.get('3D Model')
        foot_name = attributes.get('Supplier Footprint', code)

        if not model_id:
            print("⚠️ 该器件没有关联 3D 模型。")
            return

        # 3. 解析模型路径
        print(f"[3/4] 解析模型路径...")
        r2 = requests.post('https://pro.lceda.cn/api/components/searchByIds?forceOnline=1', 
                           data={'uuids[]': model_id, 'dataStr': 'yes', 'path': DEFAULT_PATH}, headers=headers)
        data_str = r2.json().get('result', [{}])[0].get('dataStr', '')
        model_id_final = json.loads(data_str).get('model')

        # 4. 下载并保存
        print(f"[4/4] 正在下载并保存 STEP 文件...")
        r3 = requests.get(f"https://modules.lceda.cn/qAxj6KHrDKw4blvCG8QJPs7Y/{model_id_final}", headers=headers)
        
        if r3.status_code == 200:
            # 应用新的命名规则
            safe_foot_name = sanitize_filename(foot_name)
            filename = f"{safe_foot_name}.step"
            
            # 去掉可能出现的连续下划线，让名字更好看（可选）
            filename = re.sub(r'_{2,}', '_', filename)
            
            with codecs.open(filename, 'w', 'utf-8') as f:
                f.write(r3.text)
            print(f"\n✅ 成功！文件已保存为: {filename}")
        else:
            print(f"❌ 下载失败，状态码: {r3.status_code}")

    except Exception as e:
        print(f"\n❌ 程序出错: {e}")

if __name__ == "__main__":
    try:
        download_lceda_model()
    finally:
        print("\n" + "=" * 50)
        input("程序执行完毕，按 [Enter] 键退出窗口...")
