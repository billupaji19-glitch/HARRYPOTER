import requests, random, time, re
from faker import Faker
from tqdm import tqdm
import telebot
from telebot import types
from telebot.handler_backends import State, StatesGroup

TOKEN = "8355089718:AAFJutnHDoJKpn803qo3Oh4LYHMTE5Q0vzw"  

bot = telebot.TeleBot(TOKEN)
fake = Faker()

# States for conversation
class ReportStates(StatesGroup):
    username = State()


def load_reports():
    with open("report.txt", "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def is_valid_username(username):
    try:
        response = requests.get(f"https://t.me/{username}", timeout=5)
        return "tgme_page_title" in response.text
    except:
        return False


def generate_data(username, message):
    name = fake.name()
    email = fake.email().split("@")[0] + "@" + random.choice(["gmail.com", "yahoo.com", "outlook.com", "rediffmail.com"])
    number = '7' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
    final_msg = message.replace("@username", f"@{username}")
    return {
        "message": final_msg,
        "legal_name": name,
        "email": email,
        "phone": number,
        "setln": ""
    }, name, email, number, final_msg


def load_proxies():
    try:
        with open("NG.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def send_data(data, proxy=None):
    headers = {
        "Host": "telegram.org",
        "origin": "https://telegram.org", 
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0",
        "referer": "https://telegram.org/support"
    }
    try:
        proxies = None
        if proxy:
            proxies = {
                'http': f'socks4://{proxy}',
                'https': f'socks4://{proxy}'
            }
        res = requests.post("https://telegram.org/support", data=data, headers=headers, proxies=proxies, timeout=10)
        success = "Thank you" in res.text or res.status_code == 200
        return success, proxy if proxy else "direct"
    except:
        return False, proxy if proxy else "direct"


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Welcome! Please enter the @username or channel/group you want to report (without @): \n┏━━━━━━━━━━━━━━━━━━━━━\n┣ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴍʏ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ\n┣𝐃𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫 ➥ @NGYT777GG :")
    bot.set_state(message.from_user.id, ReportStates.username, message.chat.id)


@bot.message_handler(state=ReportStates.username)
def handle_username(message):
    username = message.text.strip().lstrip('@')
    
    if not re.match(r'^[a-zA-Z0-9_]{5,32}$', username):
        bot.send_message(message.chat.id, "❌ Invalid username format.")
        bot.delete_state(message.from_user.id, message.chat.id)
        return

    bot.send_message(message.chat.id, "🔍 Checking if the username exists...")
    if not is_valid_username(username):
        bot.send_message(message.chat.id, "❌ Username not available on Telegram.")
        bot.delete_state(message.from_user.id, message.chat.id)
        return

    bot.send_message(message.chat.id, "✅ Username is valid. Starting report process...")

    # Begin reporting
    reports = load_reports()
    total = len(reports)
    success_count = 0
    progress_message = bot.send_message(message.chat.id, "📤 Starting reports...")

    report_log = []
    proxies = load_proxies()
    proxy_index = 0
    success_by_proxy = {}
    
    for i, msg in enumerate(reports):
        form_data, name, email, number, final_msg = generate_data(username, msg)
        proxy = proxies[proxy_index] if proxies else None
        success, used_proxy = send_data(form_data, proxy)
        
        if success:
            success_count += 1
            success_by_proxy[used_proxy] = success_by_proxy.get(used_proxy, 0) + 1
            report_log.append(f"Report {i+1}:\nName: {name}\nEmail: {email}\nPhone: {number}\nProxy: {used_proxy}\nMessage: {final_msg}\n---\n")
        
        if proxies:
            proxy_index = (proxy_index + 1) % len(proxies)
        time.sleep(2) 

        percent = int(((i + 1) / total) * 100)
        progress_bar = "█" * (percent // 10) + "▒" * (10 - (percent // 10))
        proxy_stats = "\n".join(f"🌐 {p}: {c} successful" for p, c in success_by_proxy.items())
        
        try:
            bot.edit_message_text(
                f"📊 Progress: [{progress_bar}] {percent}%\n📤 Sent: {i+1}/{total}\n\n{proxy_stats}",
                message.chat.id,
                progress_message.message_id
            )
        except:
            pass
        
        if len(report_log) > 0 and len(report_log) % 50 == 0:
            with open(f"reports_{username}.txt", "w", encoding="utf-8") as f:
                f.writelines(report_log)
            try:
                with open(f"reports_{username}.txt", "rb") as doc:
                    bot.send_document(
                        message.chat.id,
                        doc,
                        caption=f"📋 Report details for {success_count} reports"
                    )
            except:
                pass
        
        if success_count > 0 and success_count % 50 == 0:
            bot.send_message(message.chat.id, f"✅ Successfully sent {success_count} reports!")

    try:
        bot.edit_message_text(
            f"✅ Complete!\n📊 Progress: [██████████] 100%\n📨 Total successful reports: {success_count}/{total}",
            message.chat.id,
            progress_message.message_id
        )
    except:
        bot.send_message(message.chat.id, f"✅ Complete!\n📨 Total successful reports: {success_count}/{total}")
    
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(commands=['cancel'])
def cancel(message):
    bot.send_message(message.chat.id, "❌ Cancelled.")
    bot.delete_state(message.from_user.id, message.chat.id)


if __name__ == "__main__":
    bot.enable_save_next_step_handlers(delay=2)
    bot.load_next_step_handlers()
    bot.infinity_polling()
