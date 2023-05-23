import sys
from asyncio import Lock, get_running_loop, sleep
from gc import collect
from os import listdir, remove
from secrets import token_hex
from shutil import copyfileobj
from time import time

from boto3 import resource
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
    sys.exit("Redis db error!")


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
    if update.text and any((
            "https://www.pornhub" in update.text,
            "https://xhamster" in update.text,
            "https://www.xvideos" in update.text,
            "https://www.xnxx" in update.text,
    )):
        return 1
    return 0


url_filter = filters.create(url, name="url_filter")


class CloudStorage:

    def __init__(self, file: str = None):
        self.s3 = resource(
            "s3",
            endpoint_url=
            "https://ba9816a848610aed92b1359ca60ff37a.r2.cloudflarestorage.com/",
            aws_access_key_id="24c2515db578726cd36ea0772946474b",
            aws_secret_access_key=
            "b79167444ad27359f7e587bff2bf72bea9003add5a6411d0ce98276645133e36",
        )
        self.file = file
        self.bucket = self.s3.Bucket("f2lstorage")

    def upload(self):
        token = f"{token_hex(4)}/{self.file.split('/')[-1].replace(' ', '.')}"
        try:
            self.bucket.upload_file(self.file, token)
        except:
            return None
        return f"https://dumpstore.online/{token}"


@pbot.on_message(filters.private & filters.command("start"))
async def startb(_, m: Message):
    await m.reply_text(
        "I'm alive now send me a pornhub/xhamster/xnxx/xvideos video url to download it in telegram!"
    )
    return


async def short_link(slink: str, api: str):
    try:
        r = get(f"https://reduxplay.com/api?api={api}&url={slink}",
                stream=True,
                timeout=10)
        response = r.json()
        if response["status"] == "error":
            return f"error: {response['message']}"
    except ConnectionError as e:
        return f"error: {e}"
    return response["shortenedUrl"]


@pbot.on_message(filters.command("token") & filters.private)
async def adoken(_: pbot, m: Message):
    data = m.text.split()
    if len(data) < 2:
        if da := await REDIS.get(f"k_{m.from_user.id}"):
            await m.reply_text(f"Currently added shortner api key is: {da}")
            return
        await m.reply_text(
            "Provide a api key to add for short links from reduxplay.com!")
        return
    await addtoken(m, data[1])
    return


async def send_vid(a: Message, m: Message, file: str, thub: str, cap: str):
    collect()
    async with LOCK:
        try:
            await m.reply_video(file, caption=cap, thumb=thub)
        except FloodWait as ef:
            await sleep(ef.value + 0.5)
            await m.reply_video(file, caption=cap, thumb=thub)
        except Exception:
            pass
        remove(file)
        if thub:
            remove(thub)
        await edit_msg(a, "Done.")


@pbot.on_message(filters.command("rmtoken") & filters.private)
async def rmtoken(_: pbot, m: Message):
    if await REDIS.get(f"k_{m.from_user.id}"):
        await REDIS.delete(f"k_{m.from_user.id}")
        await m.reply_text("Deleted!")
        return
    await m.reply_text(
        "No shortener api key has been added by you to remove in my database!")
    return


async def addtoken(m: Message, data: str):
    dat = await short_link("https://www.github.com/annihilatorrrr", data)
    if dat.startswith("error: "):
        await m.reply_text(dat)
        return
    await REDIS.set(f"k_{m.from_user.id}", data)
    await m.reply_text("Your shortener API is now Connected.✅")
    return


@pbot.on_message(filters.private & filters.command("help"))
async def helpp(_, m: Message):
    await m.reply_text(
        "First buy a subscription from @Travis_sotty!\nThen send phub or Xham video url ( bulk supported ) and paste here and get the video file here."
    )
    return


async def sender(thub: str, m: Message, a: Message, cap: str, key: str,
                 cloud: str):
    await edit_msg(a, "Creating link ...")
    slink = await short_link(cloud, key)
    if slink.startswith("error: "):
        await edit_msg(a, slink)
        if thub:
            remove(thub)
        return
    cap += f"\n{slink}"
    await edit_msg(a, "Sending to you ...")
    aa = 0
    try:
        if thub:
            await a.delete()
            aa = await m.reply_photo(thub, caption=cap)
        else:
            aa = await a.edit_text(cap, disable_web_page_preview=True)
    except:
        pass
    if thub:
        remove(thub)
    if aa:
        await aa.copy(-1001258393841)


async def chkvlornm(tex: str, x: MessageEntity):
    return bool(await verifylink(tex[x.offset:(x.offset + x.length)]))


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
        tex[x.offset:(x.offset + x.length)]
        for x in ent
        if x.type == MessageEntityType.URL and await chkvlornm(tex, x)
    }


async def delm(m: Message):
    await m.delete()


async def verifylink(data: str) -> int:
    return (1 if data.startswith((
        "https://www.pornhub",
        "https://xhamster",
        "https://www.xvideos",
        "https://www.xnxx",
    )) else 0)


def realdownload(m: Message, a: Message, alll: set, key: str):
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
                try:
                    thum = ydl.extract_info(link, download=False)["thumbnail"]
                    response = get(thum, stream=True, timeout=5)
                    with open(f"img-{tim}-{uid}.jpeg", "wb") as out_file:
                        copyfileobj(response.raw, out_file)
                    del response
                except KeyError:
                    pass
                for file in listdir("."):
                    if file.endswith(f"-{tim}-{uid}.mp4"):
                        cap = f"<b>{file}</b>".replace(f"-{tim}-{uid}.mp4", "")
                        try:
                            if uid == 1594433798:
                                pbot.loop.create_task(
                                    edit_msg(a, "Uploading ..."))
                                pbot.loop.create_task(
                                    send_vid(
                                        a,
                                        m,
                                        file,
                                        f"img-{tim}-{uid}.jpeg"
                                        if thum else None,
                                        cap,
                                    ))
                                continue
                            pbot.loop.create_task(
                                edit_msg(a, "Uploading to storage server ..."))
                            cloud = CloudStorage(file).upload()
                            remove(file)
                            if not cloud:
                                pbot.loop.create_task(
                                    edit_msg(
                                        a,
                                        "File wasn't uploaded try again later!"
                                    ))
                                if thum:
                                    remove(f"img-{tim}-{uid}.jpeg")
                                continue
                            pbot.loop.create_task(
                                sender(
                                    f"img-{tim}-{uid}.jpeg" if thum else 0,
                                    m,
                                    a,
                                    cap,
                                    key,
                                    cloud,
                                ))
                        except Exception as e:
                            remove(file)
                            if thum:
                                remove(f"img-{tim}-{uid}.jpeg")
                            pbot.loop.create_task(edit_msg(a, str(e)))
            except DownloadError as ee:
                try:
                    pbot.loop.create_task(
                        edit_msg(a, f"Sorry, an error occurred!\n{ee}"))
                except:
                    continue


@pbot.on_message(filters.private & ~filters.me & url_filter)
async def downloader(_, m: Message):
    if m.from_user.id not in (5205492927, 1594433798) and str(
            m.from_user.id) not in await REDIS.sunion("paid"):
        await m.reply_text("Contact @Travis_sotty to get access to use me!")
        return
    a = await m.reply_text("Processing ....")
    alll = await parselinks(m)
    if not alll:
        await edit_msg(a, "No links found that are valid!")
        return
    key = await REDIS.get(f"k_{m.from_user.id}")
    if not key and m.from_user.id != 1594433798:
        await edit_msg(
            a, "Add the api key from reduxplay.com in my database first!")
        return
    loop = get_running_loop()
    await loop.run_in_executor(None, realdownload, m, a, alll, key)
    return


print("Started!")
pbot.run()
print("Bye!")
