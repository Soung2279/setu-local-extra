# setu-local-extra
## 涩图

/>>> [前往更新日志](#更新日志) <<<\

***

### 功能介绍

**HoshinoBot** 的 ``setu`` 魔改版，本地图库和在线图片API并行

比原版多的功能有：
- 支持 **R18** 与 **非R18** 分开发送
- 整合 **[LoliconAPI](https://api.lolicon.app/#/setu)** ，可使用指定词在线搜索涩图
- 自助 **重置** 日上限次数
- 可自定义 **撤回** 图片
- 可 **检查** 涩图发送情况与本地涩图文件数量
- ……

### 安装

直接将本文件（setu.py），替换到``hoshino/modules/setu/``

或者在``hoshino/modules/``中新建文件夹，将本文件放入其中，作为新插件使用。

### 指令

- **`[涩图]`** 从 **本地** 图库中随机发送一张>>>**支持正则匹配** ``^[色涩瑟][图圖]$``
- **`[来份XXX涩图]`** 从 **[LoliconAPI](https://api.lolicon.app/#/setu)** 远程请求一张符合关键词的涩图>>>**支持正则匹配** ``^[来來发發给給][张張个個幅点點份丶][色涩瑟][图圖]$``
> - 若不指定关键字，则从 **本地** 图库中随机发送一张

- **`[换弹夹@qq]`** 自助 ``（priv.ADMIN）`` 重置次数，可自行更改使用权限
- **`[检查本地涩图]`** ``（priv.ADMIN）`` 检查本地涩图运行信息，包括本地涩图文件数量，查看设置的参数，如撤回时间，每日上限次数等
- **`[清理涩图缓存]`**  清除翻转处理后的缓存图片
- **`[tssetu]`** #测试指令，指令格式 ``tssetu r18参数-tag`` 用来检查远程POST连通性与CQHttp通信

### 自定义

以下全局变量可自行设置：

```python
use_r18 = 0                                               #0-非R18；1-R18
search_mode = "or"                                        #or-'或'模式；and-'与'模式，详见下方
main_path = config.RES_DIR                                #填写在 hoshino/config/__bot__.py里的'RES_DIR'资源库路径
setu_path = f"{main_path}/img/setu/"                      #非R18存放路径
setu_path_r18 = f"{main_path}/img/setu/lolicon_r18/"      #R18存放路径
circle_pic = True                                         #True-翻转图片；False-不翻转图片（规避风控）
overturn_setu_path = f"{setu_path}cache/"                 #翻转图片缓存路径
_max = 30                                                 #每日上限
_nlmt = DailyNumberLimiter(_max)
_cd = 5                                                   #单次冷却时长(s)
_flmt = FreqLimiter(_cd)
recall_pic = True                                         #True-撤回涩图；False-不撤回涩图
PIC_SHOW_TIME = 30                                        #撤回时长(s)，图片经过此时间后才会撤回
online_size = "regular"                                   #original-发送原图；regular-发送正常；small-发送小图；详见下方
pixiv_proxy = "i.pixiv.re"                                #Pixiv代理
```

> **search_mode** 请参考Lolicon API v2文档中 [请求-tag](https://api.lolicon.app/#/setu?id=tag) 一节

> **online_size** 请参考Lolicon API v2文档中 [请求-size](https://api.lolicon.app/#/setu?id=size) 一节

以下内容可进一步更改：

```python
#第90行 Line90
payload = {
    "r18":use_r18,
    "num":1,
    "tag":str_ex,
    "size":online_size,
    "proxy":pixiv_proxy,
    "dsc":"false"                                         #缩写/简称转换，设置为true则禁用转换，详见下方
    }
```

> **dsc** 请参考Lolicon API v2文档中 [请求-dsc](https://api.lolicon.app/#/setu?id=dsc) 一节

```python
#第350行 Line350
svsc = Service(name = '_setu_cache_',use_priv = priv.NORMAL,manage_priv = priv.SUPERUSER,visible = False,enable_on_default = True,bundle = 'advance',help_ = '定时清理涩图缓存')
@svsc.scheduled_job('cron', hour='20', minute='00')       #定时任务：每天20点定时清理翻转图片缓存
async def clean_cache_auto():                             #默认为注释状态，可取消注释
    path = f"{setu_path}cache/"
    RemoveDir(path)
    sv.logger.warning(f"定时清理本地涩图缓存已执行")
```

> 可参考NoneBot v1文档中 [添加计划任务-定时发送消息](https://docs.nonebot.dev/guide/scheduler.html#%E5%AE%9A%E6%97%B6%E5%8F%91%E9%80%81%E6%B6%88%E6%81%AF) 一节


### 其它

[Lolicon API v2文档](https://api.lolicon.app/#/setu?id=api-v2)

made by [Soung2279@Github](https://github.com/Soung2279/)

### 鸣谢

[HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot)

[Lolicon API](https://api.lolicon.app/#/)

***

### 更新日志

##### 2022-8-30

因持久化问题，去除 ``查看本地涩图调用次数`` 功能

新增  整合 [Lolicon API v2](https://api.lolicon.app/#/)，现在可以使用关键词搜图功能。

将R18涩图独立文件路径

##### 2021/9/21

新增  翻转图片发送  来规避风控

新增  手动清理与定时（20点）清理翻转图片缓存

##### 2021/8/15

合并 ``查看本地涩图配置`` 与 ``查看本地涩图调用次数`` ，新指令为 ``检查本地涩图``
