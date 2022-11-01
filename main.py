from datetime import datetime
import vk_api, time, requests
from config import vk_api_token, chats, tg_api_token, tg_chat_id
from vk_api.longpoll import VkLongPoll, VkEventType
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler

bot = Bot(token=tg_api_token)
dp = Dispatcher(bot)
vk_session = vk_api.VkApi(token=vk_api_token)
longpoll = VkLongPoll(vk_session, preload_messages=True)
vk = vk_session.get_api()

def download_file(url):
    req = requests.get(url, allow_redirects=True)
    left = url.rfind('/')
    right = url.rfind('?')
    file_name = ""
    if right == -1:
        file_name = url[left::]
    else:
        file_name = url[left + 1:right:]
    print(file_name)
    open(file_name, "wb").write(req.content)
    return file_name

async def check():
    last_time = time.time()
    for event in longpoll.listen():
        #print(event.type)
        if event.type == VkEventType.MESSAGE_NEW:
            for chat in chats:
                if chat[0] == event.chat_id and event.user_id in chat[1]:
                    media = types.MediaGroup()
                    user = vk_session.method("users.get", {"user_ids": event.message_data['from_id']})
                    chat_title = vk.messages.getConversationsById(peer_ids=2000000000+event.chat_id,
                            extended=1)['items'][0]['chat_settings']['title']
                    sender_message = "<b>" + user[0]['first_name'] + ' ' + user[0]['last_name'] + " from " + chat_title + "</b>: " + "\n"

                    forward_messages_text = ""
                    reply_messages_text = ""

                    if len(event.message_data['fwd_messages']) > 0:
                        forward_messages_text = event.message_data['fwd_messages'][0]['text']
                        if len(forward_messages_text) > 50:
                            forward_messages_text = forward_messages_text[:50:] + "..."
                    
                    if 'reply_message' in event.message_data:
                        reply_messages_text = event.message_data['reply_message']['text']
                        if len(reply_messages_text) > 50:
                            reply_messages_text = reply_messages_text[:50:] + "..."

                    msg_text = ""
                    if len(event.message_data['text']) > 0:
                        msg_text = event.message_data['text']

                    if len(forward_messages_text) > 0:
                        await bot.send_message(tg_chat_id, sender_message + msg_text + "\n\n" + "<i><b>forward: </b>" + forward_messages_text + "</i>", parse_mode=types.ParseMode.HTML)
                    elif len(reply_messages_text) > 0:
                        await bot.send_message(tg_chat_id, sender_message + msg_text + "\n\n" + "<i><b>reply: </b>" + reply_messages_text + "</i>", parse_mode=types.ParseMode.HTML)
                    elif len(event.message) > 0:
                        await bot.send_message(tg_chat_id, sender_message + msg_text, parse_mode=types.ParseMode.HTML)

                    print(event.message_data)

                    for item in event.message_data['attachments']:
                        if 'wall' in item:
                            wall_text = item['wall']['text']
                            if len(wall_text) > 450:
                                wall_text = wall_text[:450:] + "..."
                            wall_url = 'https://vk.com/wall' + str(item['wall']['from_id']) + '_' + str(item['wall']['id'])
                            await bot.send_message(tg_chat_id, sender_message + "Прикреплённый пост, ссылка: " + wall_url + "\n\n" + "<i>" + wall_text + "</i>", parse_mode=types.ParseMode.HTML)
                        if 'photo' in item:
                            media.attach_photo(item['photo']['sizes'][len(item['photo']['sizes']) - 1]['url'], caption=sender_message, parse_mode=types.ParseMode.HTML)
                        if 'video' in item:
                            video_link = "https://vk.com/video" + str(item['video']['owner_id']) + "_" + str(item['video']['id'])
                            await bot.send_message(tg_chat_id, "<i>Если бы ВК позволяло, то здесь было бы видео</i>\n" + video_link, parse_mode=types.ParseMode.HTML)
                        if 'audio' in item:
                            await bot.send_message(tg_chat_id, "<i>Если бы ВК позволяло, то здесь бы была песня</i>\n" + item['audio']['artist'] + " - " + item['audio']['title'], parse_mode=types.ParseMode.HTML)
                            print(item['audio'])
                        if 'doc' in item:
                            url = requests.get(item['doc']['url'], allow_redirects=True).url
                            print(url)
                            file_name = download_file(url)
                            try:
                                media.attach_document(types.InputFile(file_name), caption=sender_message, parse_mode=types.ParseMode.HTML)
                            except:
                                pass
                        
                    if len(media.media) > 0:
                        await bot.send_media_group(tg_chat_id, media=media)

        if time.time() - last_time > 1000000000:
            break
    
        
if __name__ == '__main__':
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check, 'interval', seconds=1)
    scheduler.start()

    executor.start_polling(dp, skip_updates=True)

    
