from asyncio import events
import os
import random
import asyncio
import time
from  datetime import datetime

from nonebot.exceptions import CQHttpError

import hoshino
from hoshino import R, Service, priv
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino.typing import CQEvent

_max = 99  #每人日调用上限(次)
_nlmt = DailyNumberLimiter(_max)

_cd = 3  #调用间隔冷却时间(s)
_flmt = FreqLimiter(_cd)

recall_pic = True  #是否撤回图片
PIC_SHOW_TIME = 40  #多少秒后撤回图片

SETU_SETUP_TEXT = f'日上限{_max}次\n调用冷却{_cd}s\n是否撤回图片{recall_pic}\n{PIC_SHOW_TIME}s后撤回图片'

sv_help = '''
本地涩图，基础版的涩图。图库质量高
- [来点好看的/来点好康的]
- [换弹夹]  自助重置上限
- [查看本地涩图配置]  查看提供方配置设定
- [查看本地涩图调用次数]  查看本地涩图被所有使用者调用的次数
'''.strip()

sv = Service(
    name = '本地涩图',  #功能名
    use_priv = priv.NORMAL, #使用权限   
    manage_priv = priv.ADMIN, #管理权限
    visible = True, #是否可见
    enable_on_default = True, #是否默认启用
    bundle = '通用', #属于哪一类
    help_ = sv_help #帮助文本
    )

@sv.on_fullmatch(["帮助本地涩图"])
async def bangzhu_setu(bot, ev):
    await bot.send(ev, sv_help, at_sender=True)


@sv.on_fullmatch(["查看本地涩图配置", "查看本地涩图设置", "查看setu设置", "查看setu配置"])
async def setu_setup_notice(bot, ev):
    now = datetime.now()  #获取当前时间
    hour = now.hour  #获取当前时间小时数
    minute = now.minute  #获取当前时间分钟数
    hour_str = f' {hour}' if hour<10 else str(hour)
    minute_str = f' {minute}' if minute<10 else str(minute)
    if not priv.check_priv(ev, priv.ADMIN):
        sv.logger.warning(f"非管理者：{ev.user_id}尝试于{hour_str}点{minute_str}分查看本地涩图配置")  #记录在Log里面
        await bot.send(ev, SETU_SETUP_TEXT)
    else:
        await bot.send(ev, SETU_SETUP_TEXT)

calltime = 0  #初始化调用次数

def set_callact(func):
    global calltime  #作为全局变量使用
    calltime = 0
    def count_callact():
        func()
        global calltime
        calltime += 1
    return count_callact

@set_callact
def callact_mark():  #调用次数记录
    pass

@sv.on_fullmatch(('查看本地涩图调用次数', '查询本地涩图调用次数', '查询setu调用'))
async def testdef(bot, ev):
    now = datetime.now()  #获取当前时间
    hour = now.hour  #获取当前时间小时数
    minute = now.minute  #获取当前时间分钟数
    hour_str = f' {hour}' if hour<10 else str(hour)
    minute_str = f' {minute}' if minute<10 else str(minute)
    if not priv.check_priv(ev, priv.ADMIN):
        sv.logger.warning(f"{ev.user_id}尝试于{hour_str}点{minute_str}分查看本地涩图调用次数, 已拒绝")
        not_allowed_msg = f"权限不足。"
        await bot.send(ev, not_allowed_msg, at_sender=True)
    else:
        CALLACT_TEXT = f'监测函数名：setu\n当前时间{now}\n自HoshinoBot上次启动以来，setu已被调用{calltime}次。\n\n#注意：此调用次数非本群次数，是bot所有使用者的公共次数'
        await bot.send(ev, CALLACT_TEXT, at_sender=True)

setu_folder = R.img('setu/').path

def setu_gener():
    while True:
        filelist = os.listdir(setu_folder)
        random.shuffle(filelist)
        for filename in filelist:
            if os.path.isfile(os.path.join(setu_folder, filename)):
                yield R.img('setu/', filename)

setu_gener = setu_gener()

def get_setu():
    return setu_gener.__next__()

@sv.on_fullmatch(('来点好看的', '来点好康的'))
async def setu(bot, ev):
    uid = ev['user_id']
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    hour_str = f' {hour}' if hour<10 else str(hour)
    minute_str = f' {minute}' if minute<10 else str(minute)
    if not _nlmt.check(uid):
        EXCEED_NOTICE = f'截止{hour_str}点{minute_str}分，您已经冲过{_max}次了，请明日再来或请求群管重置次数哦！'
        await bot.send(ev, EXCEED_NOTICE, at_sender=True)
        return
    if not _flmt.check(uid):
        await bot.send(ev, f"您冲得太快了，有{_cd}秒冷却哦", at_sender=True)
        return
    
    _flmt.start_cd(uid)
    _nlmt.increase(uid)

    pic = get_setu()

    try:
        if recall_pic == True:  #简陋的是否撤回判断
            callact_mark()  #引入记录
            msg = await bot.send(ev, pic.cqcode)
            recall = await bot.send(ev, f"{PIC_SHOW_TIME}s后将撤回图片")

            await asyncio.sleep(PIC_SHOW_TIME)

            await bot.delete_msg(message_id=msg['message_id'])
            await bot.delete_msg(message_id=recall['message_id'])
        else:
            await bot.send(ev, pic.cqcode)
    
    except CQHttpError:
        sv.logger.error(f"发送图片{pic.path}失败")
        try:
            await bot.send(ev, '涩图太涩，发不出去勒...')
        except:
            pass


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