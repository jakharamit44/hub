import sys
from asyncio import Lock, get_running_loop, sleep
from gc import collect
from os import listdir, remove
from shutil import copyfileobj
from time import time

from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType
from pyrogram.errors import FloodWait
from pyrogram.types import Message, MessageEntity
from redis import RedisError
from redis.asyncio import Redis

pbot = Client(
    "dlbot",
    api_id=6,
    api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e",
    bot_token="5884751568:AAF-77WviAnRIgssCQ5VEj8kxQ1QgAl6Pu4",
)
LOCK = Lock()
REDIS = Redis.from_url(
    "redis://default:nzyNIGtMjLPmiaKZZq4pZDwLvHrplRgL@redis-16257.c244.us-east-1-2.ec2.cloud.redislabs.com:16257",
    decode_responses=True,
)
LOG_CHANNEL = -1001662444881  # Replace with your log channel ID

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
        self.file = file

    def upload(self):
        # Implement your file upload logic here
        # Replace this with your preferred file storage/upload method
        # Return the direct file URL after uploading
        return None


@pbot.on_message(filters.private & filters.command("start"))
async def startb(_, m: Message):
    await m.reply_text(
        "I'm alive now! Send me a Pornhub/Xhamster/Xnxx/Xvideos video URL to download it in Telegram!"
    )


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


@pbot.on_message(filters.command("token") & filters.private)
async def adoken(_: pbot, m: Message):
    await m.reply_text("Token functionality has been removed.")
    return


@pbot.on_message(filters.command("rmtoken") & filters.private)
async def rmtoken(_: pbot, m: Message):
    await m.reply_text("Token functionality has been removed.")
    return


@pbot.on_message(filters.command("help") & filters.private)
async def help(_: pbot, m: Message):
    await m.reply_text(
        "Just send me a Pornhub/Xhamster/Xnxx/Xvideos video URL to download it in Telegram!"
    )


@pbot.on_message(url_filter)
async def downloader(_, m: Message):
    entity = None
    for ent in m.entities:
        if ent.type == MessageEntityType.TEXT_LINK:
            entity = ent.url
            break
        elif ent.type == MessageEntityType.URL:
            entity = m.text[ent.offset : ent.offset + ent.length]
            break
    if not entity:
        return

    try:
        await m.reply_text("Downloading video...")
        file_name = f"{int(time())}.mp4"
        thumb_name = f"{int(time())}.jpg"

        # Implement your download logic here
        # Download the video using the provided URL and save it as 'file_name'
        # Optionally, download the video thumbnail and save it as 'thumb_name'

        cloud_storage = CloudStorage(file_name)
        direct_link = cloud_storage.upload()

        if direct_link:
            await send_vid(m, m, direct_link, thumb_name, entity)
        else:
            await edit_msg(m, "Error occurred while uploading the video.")
    except Exception as e:
        await edit_msg(m, f"Error occurred while downloading the video: {str(e)}")


@pbot.on_message(filters.command("omnitrix") & filters.user([123456789, 987654321]))
async def omnitrix(_, m: Message):
    await m.reply_text("Omnitrix command functionality has been removed.")
    return


@pbot.on_message(filters.command("nope") & filters.user([123456789, 987654321]))
async def nope(_, m: Message):
    await m.reply_text("Nope command functionality has been removed.")
    return


@pbot.on_message(filters.command("omni") & filters.user([123456789, 987654321]))
async def omni(_, m: Message):
    await m.reply_text("Omni command functionality has been removed.")
    return


@pbot.on_message(filters.command("del") & filters.user([123456789, 987654321]))
async def delm(_, m: Message):
    if len(m.command) > 1:
        try:
            chat_id = m.command[1]
            async for msg in pbot.USER.search_messages(chat_id, limit=1):
                await msg.delete()
            await m.delete()
        except Exception:
            pass
    else:
        await m.reply_text("Provide a valid chat ID.")


@pbot.on_message(filters.command("clean") & filters.user([123456789, 987654321]))
async def clean(_, m: Message):
    chat_id = m.chat.id
    if len(m.command) > 1 and m.command[1] == "force":
        try:
            await m.delete()
        except Exception:
            pass
        count = 0
        async for msg in pbot.USER.search_messages(chat_id):
            try:
                await msg.delete()
                count += 1
            except Exception:
                pass
        await m.reply_text(f"Cleaned {count} messages in {chat_id}.")
    else:
        count = 0
        async for msg in pbot.USER.search_messages(chat_id, from_user="me"):
            if msg.text and msg.text.startswith("Downloading video..."):
                try:
                    await msg.delete()
                    count += 1
                except Exception:
                    pass
        await m.reply_text(f"Cleaned {count} messages in {chat_id}.")


@pbot.on_message(filters.command("count") & filters.user([123456789, 987654321]))
async def count(_, m: Message):
    chat_id = m.chat.id
    count = 0
    async for _ in pbot.USER.search_messages(chat_id):
        count += 1
    await m.reply_text(f"Total messages in {chat_id}: {count}.")


@pbot.on_message(filters.command("logs") & filters.user([123456789, 987654321]))
async def logs(_, m: Message):
    await m.reply_text("Logs command functionality has been removed.")
    return


@pbot.on_message(filters.command("dellogs") & filters.user([123456789, 987654321]))
async def dellogs(_, m: Message):
    if len(m.command) > 1:
        try:
            log_chat_id = int(m.command[1])
            count = 0
            async for msg in pbot.USER.search_messages(log_chat_id):
                try:
                    await msg.delete()
                    count += 1
                except Exception:
                    pass
            await m.reply_text(f"Cleaned {count} logs in {log_chat_id}.")
        except ValueError:
            await m.reply_text("Provide a valid log chat ID.")
    else:
        await m.reply_text("Provide a log chat ID.")


@pbot.on_message(filters.private & filters.command("stats"))
async def stats(_, m: Message):
    user_id = m.from_user.id
    chat_id = m.chat.id

    total_user_msgs = await REDIS.get(f"total_msg:{user_id}")
    if not total_user_msgs:
        total_user_msgs = 0

    total_chat_msgs = await REDIS.get(f"total_msg:{chat_id}")
    if not total_chat_msgs:
        total_chat_msgs = 0

    await m.reply_text(
        f"Total messages by you: {total_user_msgs}\nTotal messages in this chat: {total_chat_msgs}"
    )


@pbot.on_message(filters.private & filters.command("logs"))
async def get_logs(_, m: Message):
    log_chat_id = m.chat.id
    try:
        logs = []
        async for log in pbot.USER.search_messages(log_chat_id):
            logs.append(log.text)

        if logs:
            await m.reply_text("\n".join(logs))
        else:
            await m.reply_text("No logs found.")
    except Exception:
        await m.reply_text("Error occurred while retrieving logs.")


async def message_counter(_: pbot, m: Message):
    user_id = m.from_user.id
    chat_id = m.chat.id

    await REDIS.incr(f"total_msg:{user_id}")
    await REDIS.incr(f"total_msg:{chat_id}")


@pbot.on_message(filters.command("broadcast") & filters.user([123456789, 987654321]))
async def broadcast(_, m: Message):
    if len(m.command) > 1:
        text = " ".join(m.command[1:])
        chat_ids = [int(chat_id) for chat_id in await REDIS.smembers("chat_ids")]
        success = 0
        failure = 0
        for chat_id in chat_ids:
            try:
                await pbot.send_message(chat_id, text)
                success += 1
            except Exception:
                failure += 1
        await m.reply_text(
            f"Broadcast completed. Total: {len(chat_ids)}, Success: {success}, Failure: {failure}"
        )
    else:
        await m.reply_text("Provide a message to broadcast.")


@pbot.on_message(filters.private & filters.command("export") & filters.user([123456789, 987654321]))
async def export_data(_, m: Message):
    try:
        file_name = f"data_export_{int(time())}.txt"
        async with LOCK:
            async with open(file_name, "w") as f:
                chat_ids = [chat_id for chat_id in await REDIS.smembers("chat_ids")]
                for chat_id in chat_ids:
                    f.write(f"{chat_id}\n")
        with open(file_name, "rb") as f:
            await m.reply_document(f)
        remove(file_name)
    except Exception:
        await m.reply_text("Error occurred while exporting data.")


@pbot.on_message(filters.private & filters.command("import") & filters.user([123456789, 987654321]))
async def import_data(_, m: Message):
    if m.reply_to_message and m.reply_to_message.document:
        file = m.reply_to_message.document
        if file.file_size > 10 * 1024 * 1024:
            await m.reply_text("File size exceeds the limit of 10MB.")
            return
        file_name = f"data_import_{int(time())}.txt"
        await pbot.download_media(file, file_name)
        try:
            chat_ids = []
            async with LOCK:
                with open(file_name, "r") as f:
                    for line in f:
                        chat_id = line.strip()
                        if chat_id.isdigit():
                            chat_ids.append(int(chat_id))
            if chat_ids:
                await REDIS.sadd("chat_ids", *chat_ids)
                await m.reply_text("Import completed.")
            else:
                await m.reply_text("No chat IDs found in the file.")
        except Exception:
            await m.reply_text("Error occurred while importing data.")
        remove(file_name)
    else:
        await m.reply_text("Reply to a document file containing chat IDs to import.")


@pbot.on_chat_member_updated()
async def chat_member_updated(_, m: Message):
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.new_chat_members and user_id == pbot.USER.id:
        await REDIS.sadd("chat_ids", chat_id)
    elif m.left_chat_member and user_id == pbot.USER.id:
        await REDIS.srem("chat_ids", chat_id)


@pbot.on_message(filters.private)
async def private_chat(_, m: Message):
    chat_id = m.chat.id
    await REDIS.sadd("chat_ids", chat_id)


@pbot.on_message(filters.group)
async def group_chat(_, m: Message):
    chat_id = m.chat.id
    await REDIS.sadd("chat_ids", chat_id)


@pbot.on_message(filters.private & filters.command("leave") & filters.user([123456789, 987654321]))
async def leave_chat(_: pbot, m: Message):
    if m.reply_to_message and m.reply_to_message.text:
        chat_id = m.reply_to_message.text.strip()
        if chat_id.isdigit():
            await pbot.leave_chat(int(chat_id))
            await m.reply_text("Left the chat.")
        else:
            await m.reply_text("Invalid chat ID.")
    else:
        await m.reply_text("Reply to a message containing the chat ID to leave.")


async def main():
    try:
        await pbot.start()
        print("Bot started. Listening to messages...")
        await pbot.send_message(LOG_CHANNEL, "Bot started.")
        await pbot.idle()
    finally:
        await pbot.stop()


if __name__ == "__main__":
    asyncio.run(main())
