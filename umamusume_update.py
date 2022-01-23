import json
from configobj import ConfigObj
import requests
import models
import time
import unzip_file
import os

api_urls = ["https://api.github.com", "http://rpx-github-api.chieri.cc"]
github_urls = ["https://github.com", "http://rpx-github.chieri.cc"]


def timestamp_to_text(timestamp: int, _format="%Y-%m-%d %H:%M:%S"):
    if timestamp > 9999999999:
        timestamp = timestamp / 1000
    ret = time.strftime(_format, time.localtime(timestamp))
    return ret

def readobj(config: ConfigObj, section, item, default: str = '') -> str:
    try:
        res = config[section][item]
    except:
        res = default
    return res

def writeobj(config: ConfigObj, section, item, value) -> bool:
    try:
        if section not in config:
            config[section] = {}
        config[section][item] = value
        config.write()
        return True
    except:
        return False

def get_releases_data(endpoint=0):
    url = f"{api_urls[endpoint]}/repos/MinamiChiwa/umamusume-localify-developUPDATE/releases"
    response = requests.request("GET", url)
    if response.status_code != 200:
        raise RuntimeError(f"数据获取失败 {response.status_code}")

    data = json.loads(response.text)
    return [models.Release(**d) for d in data]

def get_latest_data(assets: models.t.List[models.Assets], endpoint=0):
    for asset in assets:
        if asset.name.startswith("DMMUPD") and asset.name.endswith(".zip"):
            url = asset.browser_download_url
            if endpoint != 0:
                url = url.replace(github_urls[0], github_urls[endpoint], 1)
                response = requests.get(url)
                if response.status_code != 200:
                    raise RuntimeError(f"下载失败 {response.status_code}")
                else:
                    with open("umamusume_localify_update.zip", "wb") as f:
                        f.write(response.content)
                    unzip_file.unzip_file("umamusume_localify_update.zip", "./")
        else:
            continue

def change_config_json(config_before, up_type: int):
    if up_type == 1:  # 仅更新dicts
        data_before = json.loads(config_before)
        with open("config.json", "r", encoding="utf8") as _f:
            data_after = json.load(_f)
        update_count = len(data_after["dicts"]) - len(data_before["dicts"])
        data_before["dicts"] = data_after["dicts"]
        with open("config.json", "w", encoding="utf8") as _f:
            _f.write(json.dumps(data_before, ensure_ascii=False))
        print(f"config.json - dicts 更新了 {update_count} 条资源")
    elif up_type == 2:  # 覆盖
        pass
    elif up_type == 3:  # 不更
        with open("config.json", "w", encoding="utf8") as _f:
            _f.write(config_before)


if __name__ == "__main__":
    try:
        local_config = ConfigObj("local_releases_version.ini", encoding="utf8")
        local_version = readobj(local_config, "update", "local_ver", "")
        local_version_id = int(readobj(local_config, "update", "local_id", "-1"))

        while True:
            url_point = input("请选择网络节点\n[1] github节点\n[2] 反代节点\n"
                              "若无法连接github, 可以尝试使用反代节点。请输入序号进行选择:")
            try:
                url_point = int(url_point.strip()) - 1
            except:
                print("您输入的序号有误")
            if len(api_urls) < url_point + 1:
                print("您输入的序号有误")
            else:
                break

        releases_data = get_releases_data(url_point)
        releases_data = sorted(releases_data, key=lambda x: x.published_at_timestamp)
        latest_releases = releases_data[-1]
        print(f"版本说明:\n{latest_releases.body}\n\n云端最新版本为: {latest_releases.tag_name}({latest_releases.id})")

        if local_version == "":
            print(f"未检测到本地配置")
        else:
            print(f"您本地版本为: {local_version}({local_version_id})")
            if local_version_id == latest_releases.id:
                print("本地版本已是最新版本, 若继续下载, 将覆盖现有的文件")

        if int(input("是否从云端下载? 0-否, 1-是:")):
            if os.path.isfile("config.json"):
                while True:
                    try:
                        update_config_type = int(input("\n请选择 config.json 的更新方式:\n"
                                                       "[1] 仅更新\"dicts\"(推荐)\n[2] 覆盖\n[3] 不更新\n请输入序号:"))
                        if update_config_type in [1, 2, 3]:
                            break
                        else:
                            print("您输入的序号有误")
                    except:
                        print("您输入的序号有误")

                with open("config.json", "r", encoding="utf8") as f:
                    config_json_before = f.read()
            else:
                config_json_before = "{}"
                update_config_type = -1
            print("开始下载...")
            get_latest_data(latest_releases.assets, url_point)
            writeobj(local_config, "update", "local_ver", latest_releases.tag_name)
            writeobj(local_config, "update", "local_id", str(latest_releases.id))
            change_config_json(config_json_before, update_config_type)

            print(f"本地文件已更新至: {latest_releases.tag_name}({latest_releases.id})")
        else:
            print("取消下载")
        input("按任意键退出...")
    except BaseException as e:
        print(e)
        print("更新出错")
        input("按任意键退出...")
