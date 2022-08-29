#-*- coding:utf-8 -*-
from fileinput import filename
from tabnanny import check
from time import time
import re
import os
from os.path import join, getsize
import shutil
import random
import asyncio
import time
import requests
from datetime import datetime
from PIL import Image
from nonebot import get_bot
from nonebot.exceptions import CQHttpError

import hoshino
from hoshino import R, Service, priv, config
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino.typing import CQEvent

try:
    import ujson as json
except ImportError:
    import json

#全局变量
bot = get_bot()
use_r18 = 0 #0关闭1开启
search_mode = "or"  #or或and和
main_path = config.RES_DIR
setu_path = f"{main_path}/img/setu/"
setu_path_r18 = f"{main_path}/img/setu/lolicon_r18/"
circle_pic = True   #True翻转False不翻转
overturn_setu_path = f"{setu_path}cache/"
_max = 30   #日上限
_nlmt = DailyNumberLimiter(_max)
_cd = 5   #冷却时长(s)
_flmt = FreqLimiter(_cd)
recall_pic = True   #True撤回False不撤回
PIC_SHOW_TIME = 30  #撤回时长(s)
online_size = "regular" #请求的在线涩图大小，原图为original，正常为regular，小图为small
pixiv_proxy = "i.pixiv.re"  #Pixiv代理



sv_help = '''
原生涩图进化版
- [涩图]    #随机发送1张
- [来份XXX涩图] #根据指定词进行在线搜索
- [换弹夹]  #重置使用次数
- [检查本地涩图]
- [清理涩图缓存]
'''.strip()

sv = Service(
    name = '涩图',  #功能名
    use_priv = priv.NORMAL, #使用权限   
    manage_priv = priv.ADMIN, #管理权限
    visible = True, #是否可见
    enable_on_default = True, #是否默认启用
    bundle = '通用', #属于哪一类
    help_ = sv_help #帮助文本
    )

@sv.on_fullmatch(["帮助涩图"])
async def bangzhu_setun(bot, ev):
    await bot.send(ev, sv_help)


def get_online_setu(tag):
    filename = []
    error_warn = []
    lolicon_post_info = []
    pixiv_post_info = []
    if search_mode == 'or':
        str_ex = tag.split('或')
    elif search_mode == 'and':
        str_ex = tag.split('和')
    else:
        str_ex = tag.split('或')    #默认使用'或'模式

    payload = {
        "r18":use_r18,
        "num":1,
        "tag":str_ex,
        "size":online_size,
        "proxy":pixiv_proxy,
        "dsc":"false"   #缩写/简称转换，设置为true则禁用转换
        }
    response = requests.post('https://api.lolicon.app/setu/v2', json=payload)   #使用POST请求以支持二维数组Tags

    lolicon_post_info = f'Lolicon请求状态码：{response.status_code}'
    lolicon_data = json.loads(response.text)
    lolicon_error = lolicon_data['error']
    if not lolicon_error:
        data = lolicon_data['data']
        img_pid = data[0]['pid']
        img_url = data[0]['urls'][f'{online_size}']
    else:
        error_warn = f'连接LoliconAPI：{lolicon_post_info}\nLoliconAPI响应错误：信息{lolicon_error}'
        return error_warn

    #判断是否使用R18模式，0为不使用，1为使用
    if use_r18 == 0:
        path = setu_path
    elif use_r18 == 1:
        path = setu_path_r18
    else:
        print('###WARNING###   涩图R18设置参数有误！')
        path = setu_path   #参数不规范时，使用默认路径

    r = requests.get(img_url)
    if int(r.status_code) == 200:
        pixiv_post_info = '状态码：200---OK///请求成功'
        filename = str(img_pid)+'.jpg'
        image_path = path+filename
        with open(image_path,'wb') as f:  
            f.write(r.content)
            f.close()
    else:
        pixiv_post_info = f'\n状态码：{r.status_code}\n'
        error_warn = f'连接Pixiv：{pixiv_post_info}'
        return error_warn

    error_warn = f'连接LoliconAPI：{lolicon_post_info}\n连接Pixiv状态：{pixiv_post_info}'
    return error_warn, filename

#翻转图片处理
def overturn_img(filename):
    if use_r18 == 0:
        pri_image = Image.open(f"{setu_path}{filename}")
    elif use_r18 == 1:
        pri_image = Image.open(f"{setu_path_r18}{filename}")
    else:
        setu_folder = R.img('setu/').path
        pri_image = Image.open(f"{setu_folder}{filename}")
    
    tmppath = overturn_setu_path + filename
    pri_image.rotate(180).save(tmppath)  #图片翻转180°
    output = R.img(f'setu/cache/{filename}')
    return output

'''
overturn_img = overturn_img()
def get_overturn_setu():
    return overturn_img.__next__()
'''

#随机获取1张本地图片，返回文件名
def local_setu_gener():
    if use_r18 == 0:
        setu_folder = setu_path
    elif use_r18 == 1:
        setu_folder = setu_path_r18
    else:
        setu_folder = R.img('setu/').path
    
    filelist = os.listdir(setu_folder)
    random.shuffle(filelist)
    for filename in filelist:
        if os.path.isfile(os.path.join(setu_folder, filename)):
            return filename

#正常图片处理
def base_img(filename):
    if use_r18 == 0:
        output = R.img(f'setu/{filename}')
        return output
    elif use_r18 == 1:
        output = R.img(f'setu/lolicon_r18/{filename}')
        return output
    else:
        output = R.img(f'setu/{filename}')
        return output
'''
base_img = base_img()
def get_setu():
    return base_img.__next__()
'''

@sv.on_rex(r'^[色涩瑟][图圖]$')
async def setu(bot, ev):
    uid = ev['user_id']
    if not _nlmt.check(uid):
        EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明日再来或请求群管重置次数哦！'
        await bot.send(ev, EXCEED_NOTICE, at_sender=True)
        return
    if not _flmt.check(uid):
        await bot.send(ev, f"您冲得太快了，有{_cd}秒冷却哦", at_sender=True)
        return
    
    _flmt.start_cd(uid)
    _nlmt.increase(uid)

    if circle_pic is True:
        perm = local_setu_gener()
        pic = overturn_img(perm)
    else:
        perm = local_setu_gener()
        pic = base_img(perm)

    try:
        if recall_pic == True:
            msg = await bot.send(ev, pic.cqcode)
            recall = await bot.send(ev, f"{PIC_SHOW_TIME}s后将撤回图片")
            await asyncio.sleep(PIC_SHOW_TIME)
            await bot.delete_msg(message_id=msg['message_id'])
            await bot.delete_msg(message_id=recall['message_id'])
        else:
            await bot.send(ev, pic.cqcode)
    except CQHttpError:
        sv.logger.error(f"发送图片{pic.path}失败")
        await bot.send(ev, '涩图太涩，发不出去勒...')


@sv.on_rex(r'^[来來发發给給][张張个個幅点點份丶](?P<keyword>.*?)[色涩瑟][图圖]$')
async def send_setu(bot, ev):
    uid = ev['user_id']
    if not _nlmt.check(uid):
        EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明日再来或请求群管重置次数哦！'
        await bot.send(ev, EXCEED_NOTICE, at_sender=True)
        return
    if not _flmt.check(uid):
        await bot.send(ev, f"您冲得太快了，有{_cd}秒冷却哦", at_sender=True)
        return
    
    _flmt.start_cd(uid)
    _nlmt.increase(uid)
    word = ev['match'].group('keyword').strip()

    if not word:
        if circle_pic is True:
            perm = local_setu_gener()
            pic = overturn_img(perm)
        else:
            perm = local_setu_gener()
            pic = base_img(perm)
        try:
            if recall_pic == True:
                msg = await bot.send(ev, pic.cqcode)
                recall = await bot.send(ev, f"{PIC_SHOW_TIME}s后将撤回图片")
                await asyncio.sleep(PIC_SHOW_TIME)
                await bot.delete_msg(message_id=msg['message_id'])
                await bot.delete_msg(message_id=recall['message_id'])
                #sv.logger.warning('撤回涩图成功')
            else:
                await bot.send(ev, pic.cqcode)
        except CQHttpError:
            sv.logger.error(f"发送图片{pic.path}失败")
            await bot.send(ev, '涩图太涩，发不出去勒...')
    else:
        await bot.send(ev, f'正在搜索“{word}”中...')
        try:
            setu_res = get_online_setu(word)
            #await bot.send(ev, setu_res[0]) #输出请求状态
            if not setu_res[1]: #返回空文件名，说明远程请求失败，输出错误信息
                error_recall = setu_res[0]
                await bot.send(ev, error_recall)
            else:
                if circle_pic is True:
                    pic = overturn_img(setu_res[1])
                    try:
                        if recall_pic == True:
                            msg = await bot.send(ev, pic.cqcode)
                            recall = await bot.send(ev, f"{PIC_SHOW_TIME}s后将撤回图片")
                            await asyncio.sleep(PIC_SHOW_TIME)
                            await bot.delete_msg(message_id=msg['message_id'])
                            await bot.delete_msg(message_id=recall['message_id'])
                            #sv.logger.warning('撤回涩图成功')
                        else:
                            await bot.send(ev, pic.cqcode)
                    except CQHttpError:
                        await bot.send(ev, '涩图太涩，发不出去勒...')
                else:
                    pic = base_img(setu_res[1])
                    try:
                        if recall_pic == True:
                            msg = await bot.send(ev, pic.cqcode)
                            recall = await bot.send(ev, f"{PIC_SHOW_TIME}s后将撤回图片")
                            await asyncio.sleep(PIC_SHOW_TIME)
                            await bot.delete_msg(message_id=msg['message_id'])
                            await bot.delete_msg(message_id=recall['message_id'])
                            #sv.logger.warning('撤回涩图成功')
                        else:
                            await bot.send(ev, pic.cqcode)
                    except CQHttpError:
                        await bot.send(ev, '涩图太涩，发不出去勒...')
        except CQHttpError:
            sv.logger.error(f"发送图片{pic.path}失败")
            await bot.send(ev, '涩图太涩，发不出去勒...')


# 清理文件目录
def RemoveDir(filepath):
    '''
    如果文件夹不存在就创建，如果文件存在就清空！
    '''
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    else:
        shutil.rmtree(filepath)
        os.mkdir(filepath)

# 获取文件目录大小
def getdirsize(dir):
    size = 0
    for root, dirs, files in os.walk(dir):
        size += sum([getsize(join(root, name)) for name in files])
    return size

def countFile(dir):
    tmp = 0
    for item in os.listdir(dir):
        if os.path.isfile(os.path.join(dir, item)):
            tmp += 1
        else:
            tmp += countFile(os.path.join(dir, item))
    return tmp

@sv.on_fullmatch(["清理涩图缓存", "清除setu", "清理本地涩图缓存", "清理setu", "清除涩图缓存"])
async def remove_setucache(bot, ev):
    path = f"{setu_path}cache/"
    shots_all_num = countFile(str(setu_path+"cache/"))  #同上
    shots_all_size = getdirsize(f"{setu_path}cache/")  #同上
    all_size_num = '%.3f' % (shots_all_size / 1024 / 1024)
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    hour_str = f' {hour}' if hour<10 else str(hour)
    minute_str = f' {minute}' if minute<10 else str(minute)
    if not priv.check_priv(ev, priv.SUPERUSER):   #建议使用priv.SUPERUSER
        sv.logger.warning(f"{ev.user_id}尝试于{hour_str}点{minute_str}分清空涩图缓存, 已拒绝")
        not_allowed_msg = f"权限不足。"  #权限不足时回复的消息
        await bot.send(ev, not_allowed_msg, at_sender=True)
        return
    else:
        info_before = f"当前翻转处理过的涩图有{shots_all_num}张，占用{all_size_num}Mb\n即将进行清理。"
        await bot.send(ev, info_before)

        RemoveDir(path)  #清理文件目录

        after_size = getdirsize(f"{setu_path}cache/")  #同上
        after_num = '%.3f' % (after_size / 1024 / 1024)
        info_after = f"清理完成。当前占用{after_num}Mb"
        sv.logger.warning(f"超级用户{ev.user_id}于{hour_str}点{minute_str}分清空涩图缓存")
        await bot.send(ev, info_after)

'''
svsc = Service(name = '_setu_cache_',use_priv = priv.NORMAL,manage_priv = priv.SUPERUSER,visible = False,enable_on_default = True,bundle = 'advance',help_ = '定时清理涩图缓存')
@svsc.scheduled_job('cron', hour='20', minute='00')  #每天20点定时清理
async def clean_cache_auto():
    path = f"{setu_path}cache/"
    RemoveDir(path)
    sv.logger.warning(f"定时清理本地涩图缓存已执行")
'''

#群管理自助重置日上限（可以给自己重置，可以@多人）
@sv.on_prefix(('换肾', '补肾', '换弹夹', '换蛋夹'))
async def resetsetu(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):  #权限：ADMIN, 可以改成SUPERUSER防止滥用
        await bot.send(ev, '您的权限不足！请联系群管哦~')
        return
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            _nlmt.reset(uid)
            count += 1
    if count:
        await bot.send(ev, f"已为{count}位用户重置次数！注意身体哦～")


@sv.on_fullmatch(('检查本地setu', '检查本地涩图', '检查本地色图'))
async def check_setu_local(bot, ev):
    gid = ev['group_id']
    now = datetime.now()  #获取当前时间
    hour = now.hour  #获取当前时间小时数
    minute = now.minute  #获取当前时间分钟数
    now_date = time.strftime("%Y-%m-%d", time.localtime()) #获取当前日期
    hour_str = f' {hour}' if hour<10 else str(hour)
    minute_str = f' {minute}' if minute<10 else str(minute)
    image_api = await bot.can_send_image()  #检查是否能发送图片
    image_check = image_api.get('yes')
    image_base_num = countFile(setu_path)   #获取正常涩图数量
    image_r18_num = countFile(setu_path_r18)   #获取R18涩图数量
    image_all_num = image_base_num + image_r18_num   #获取所有涩图量
    if not priv.check_priv(ev, priv.ADMIN):
        sv.logger.warning(f"来自群：{gid}的非管理者：{ev.user_id}尝试于{now_date}{hour_str}点{minute_str}分检查本地色图")
        await bot.send(ev, '一般通过群友不需要看这个啦，让管理员来试试看吧')
        return

    text1 = f"【发送权限检查】：\n是否能发送图片:{image_check}"
    text2 = f"【数据存储检查】：\n截止{now_date}，本地涩图的总存量为:{image_all_num}张\n其中，正常涩图占{image_base_num}张，R18涩图占{image_r18_num}张"
    SETU_SETUP_TEXT = f"【涩图设定情况】：\n当前bot主人设置的日上限为：{_max}次\n调用冷却为：{_cd}s\n是否撤回图片：{recall_pic}\n{PIC_SHOW_TIME}s后撤回图片\n是否启用图片翻转：{circle_pic}"
    
    checkfile = text1 + '\n' + text2
    checksetu = SETU_SETUP_TEXT

    await bot.send(ev, checkfile)
    time.sleep(2)
    await bot.send(ev, checksetu)

'''
测试用，指令格式 tssetu r18参数-tag

@sv.on_prefix(('tssetu'))
async def test_setu(bot, ev):
    input = ev.message.extract_plain_text()
    execute_input = input.split('-')
    payload = {
        "r18":int(execute_input[0]),
        "num":1,
        "tag":execute_input[1],
        "size":"small",
        }
    r = requests.post('https://api.lolicon.app/setu/v2', json=payload)
    await bot.send(ev, str(r.status_code))
    meta = json.loads(r.text)
    lolicon_error = meta['error']
    lolicon_data = meta['data']
    await bot.send(ev, f'loERROR:{lolicon_error}\nloDATA:{lolicon_data}')
    img_url = lolicon_data[0]['urls']['small']
    p = requests.get(img_url)
    filename = 'test.jpg'
    image_path = hoshino.config.RES_DIR+filename
    await bot.send(ev, str(p.status_code))
    with open(image_path,'wb') as f:  
        f.write(p.content)
        f.close()
    await bot.send(ev, R.img(image_path).cqcode)
'''