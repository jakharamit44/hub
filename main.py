from asyncio import Lock, get_running_loop, sleep
from contextlib import suppress
from gc import collect
from os import listdir, remove
from shutil import copyfileobj
from sys import exit as exiter
from time import time

from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType
from pyrogram.errors import FloodWait
from pyrogram.types import Message, MessageEntity
from redis import RedisError
from redis.asyncio import Redis
from requests import get
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError

pbot = Client(
    "dlbot",
    api_id=6,
    api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e",
    bot_token="5884751568:AAFFZRqYusquif_SPIeXyytsDQBYwDTrAeQ",
)
LOCK = Lock()
REDIS = Redis.from_url(
    "redis://default:nzyNIGtMjLPmiaKZZq4pZDwLvHrplRgL@redis-16257.c244.us-east-1-2.ec2.cloud.redislabs.com:16257",
    decode_responses=True,
)
try:
    pbot.loop.run_until_complete(REDIS.ping())
except RedisError:
    exiter("Redis db error!")


async def edit_msg(m: Message, to_edit: str):
    try:
        await m.edit_text(to_edit)
    except FloodWait as ef:
        await sleep(ef.value + 0.5)
        await m.edit_text(to_edit)
    except Exception:
        pass
    return


def url(_, __, update: Message):
    if update.text and any(
        (
            "https://www.pornhub" in update.text,
            "https://xhamster" in update.text,
            "https://www.xvideos" in update.text,
            "https://www.xnxx" in update.text,
        )
    ):
        return 1
    return 0


url_filter = filters.create(url, name="url_filter")


@pbot.on_message(filters.private & filters.command("start"))
async def startb(_, m: Message):
    await m.reply_text(
        "I'm alive now send me a pornhub/xhamster/xnxx/xvideos video url to download it in telegram!"
    )
    return


async def send_vid(a: Message, m: Message, file: str, thub: str, cap: str):
    collect()
    async with LOCK:
        aa = 0
        try:
            aa = await m.reply_video(file, caption=cap, thumb=thub)
        except FloodWait as ef:
            await sleep(ef.value + 0.5)
            aa = await m.reply_video(file, caption=cap, thumb=thub)
        except Exception:
            pass
        remove(file)
        if thub:
            remove(thub)
        await edit_msg(a, "Done.")
        if aa:
            await aa.copy(-1001955880475)
    return


@pbot.on_message(filters.private & filters.command("help"))
async def helpp(_, m: Message):
    await m.reply_text(
        "First buy a subscription from @Travis_sotty!\nThen send phub or Xham video url ( bulk supported ) and paste here and get the video file here."
    )
    return


async def chkvlornm(tex: str, x: MessageEntity):
    return bool(await verifylink(tex[x.offset : (x.offset + x.length)]))


@pbot.on_message(filters.user(5205492927) & filters.command("omnitrix"))
async def paid(_, m: Message):
    if len(m.text.split()) > 1:
        try:
            int(m.text.split()[1])
        except ValueError:
            await m.reply_text("Not a user id!")
            return
        await REDIS.sadd("paid", m.text.split()[1])
        await m.reply_text("Added!")
    else:
        await m.reply_text("Provide a user id!")
    return


@pbot.on_message(filters.user(5205492927) & filters.command("nope"))
async def unpaid(_, m: Message):
    if len(m.text.split()) > 1:
        try:
            int(m.text.split()[1])
        except ValueError:
            await m.reply_text("Not a user id!")
            return
        await REDIS.srem("paid", m.text.split()[1])
        await m.reply_text("Removed!")
    else:
        await m.reply_text("Provide a user id!")
    return


@pbot.on_message(filters.user(5205492927) & filters.command("omni"))
async def paids(_, m: Message):
    aa = "Paid list:\n"
    for x in await REDIS.sunion("paid"):
        aa += f"{x}\n"
    await m.reply_text(aa)
    return


async def parselinks(m: Message):
    ent = m.entities
    if not ent:
        return 0
    tex = m.text
    return {
        tex[x.offset : (x.offset + x.length)]
        for x in ent
        if x.type == MessageEntityType.URL and await chkvlornm(tex, x)
    }


async def delm(m: Message):
    await m.delete()


async def verifylink(data: str) -> int:
    return (
        1
        if data.startswith(
            (
                "https://www.pornhub",
                "https://xhamster",
                "https://www.xvideos",
                "https://www.xnxx",
            )
        )
        else 0
    )


def realdownload(m: Message, a: Message, alll: set):
    uid = m.from_user.id
    tim = time()
    ydl_opts = {
        "outtmpl": f"%(title)s-{tim}-{uid}.%(ext)s",
    }
    thum = 0
    with YoutubeDL(ydl_opts) as ydl:
        for link in alll:
            try:
                pbot.loop.create_task(edit_msg(a, "🧑‍🏭"))
                ydl.download([link])
                pbot.loop.create_task(edit_msg(a, "Preparing ..."))
                with suppress(KeyError):
                    thum = ydl.extract_info(link, download=False)["thumbnail"]
                    response = get(thum, stream=True, timeout=5)
                    with open(f"img-{tim}-{uid}.jpeg", "wb") as out_file:
                        copyfileobj(response.raw, out_file)
                    del response
                for file in listdir("."):
                    if file.endswith(f"-{tim}-{uid}.mp4"):
                        cap = f"<b>{file}</b>".replace(f"-{tim}-{uid}.mp4", "")
                        try:
                            pbot.loop.create_task(edit_msg(a, "Uploading ..."))
                            pbot.loop.create_task(
                                send_vid(
                                    a,
                                    m,
                                    file,
                                    f"img-{tim}-{uid}.jpeg" if thum else None,
                                    cap,
                                )
                            )
                        except Exception as e:
                            remove(file)
                            if thum:
                                remove(f"img-{tim}-{uid}.jpeg")
                            pbot.loop.create_task(edit_msg(a, str(e)))
            except DownloadError as ee:
                with suppress(Exception):
                    pbot.loop.create_task(
                        edit_msg(a, f"Sorry, an error occurred!\n{ee}")
                    )


@pbot.on_message(filters.private & ~filters.me & url_filter)
async def downloader(_, m: Message):
    if m.from_user.id not in (5205492927, 1594433798) and str(
        m.from_user.id
    ) not in await REDIS.sunion("paid"):
        await m.reply_text("Contact @Travis_sotty to get access to use me!")
        return
    a = await m.reply_text("Processing ....")
    alll = await parselinks(m)
    if not alll:
        await edit_msg(a, "No links found that are valid!")
        return
    await get_running_loop().run_in_executor(None, realdownload, m, a, alll)
    return


print("Started!")
pbot.run()
print("Bye!")


