import html
import os
import random

import aiohttp
from pyrogram import filters
from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb
from config import MONGO_DB_URI

lovebirds_db = mongodb.lovebirds
users_collection = lovebirds_db.users
gifts_collection = lovebirds_db.gifts

GIFTS = {
    "🌹": {"name": "Rose", "cost": 10, "emoji": "🌹"},
    "🍫": {"name": "Chocolate", "cost": 20, "emoji": "🍫"},
    "🧸": {"name": "Teddy Bear", "cost": 30, "emoji": "🧸"},
    "💍": {"name": "Ring", "cost": 50, "emoji": "💍"},
    "❤️": {"name": "Heart", "cost": 5, "emoji": "❤️"},
    "🌺": {"name": "Flower Bouquet", "cost": 25, "emoji": "🌺"},
    "💎": {"name": "Diamond", "cost": 100, "emoji": "💎"},
    "🎀": {"name": "Gift Box", "cost": 40, "emoji": "🎀"},
    "🌙": {"name": "Moon", "cost": 35, "emoji": "🌙"},
    "⭐": {"name": "Star", "cost": 15, "emoji": "⭐"},
    "🦋": {"name": "Butterfly", "cost": 18, "emoji": "🦋"},
    "🕊️": {"name": "Dove", "cost": 22, "emoji": "🕊️"},
    "🏰": {"name": "Castle", "cost": 80, "emoji": "🏰"},
    "🎂": {"name": "Cake", "cost": 28, "emoji": "🎂"},
    "🍓": {"name": "Strawberry", "cost": 12, "emoji": "🍓"}
}

async def get_user_data(user_id):
    try:
        user_data = await users_collection.find_one({"user_id": user_id})
        if not user_data:
            new_user = {
                "user_id": user_id,
                "coins": 50,
                "total_gifts_received": 0,
                "total_gifts_sent": 0,
                "created_at": "2025"
            }
            await users_collection.insert_one(new_user)
            return new_user
        return user_data
    except:
        return {"user_id": user_id, "coins": 0, "total_gifts_received": 0, "total_gifts_sent": 0}

async def update_user_coins(user_id, amount):
    try:
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"coins": amount}},
            upsert=True
        )
    except:
        pass

async def get_user_gifts(user_id, gift_type="received"):
    try:
        if gift_type == "received":
            gifts = await gifts_collection.find({"receiver_id": user_id}).to_list(length=None)
        else:
            gifts = await gifts_collection.find({"sender_id": user_id}).to_list(length=None)
        return gifts
    except:
        return []

def get_user_info(message):
    try:
        if not message.from_user:
            return None, None
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        return user_id, username
    except:
        return None, None

@app.on_message(filters.command(["balance", "bal"], prefixes=["/", "!", "."]))
async def balance(_, message):
    try:
        uid, username = get_user_info(message)
        if not uid:
            return
        
        user_data = await get_user_data(uid)
        
        coins = user_data["coins"]
        gifts_received = await gifts_collection.count_documents({"receiver_id": uid})
        gifts_sent = await gifts_collection.count_documents({"sender_id": uid})
        
        balance_text = f"""
💰 <b>{username}'s Account</b>
💸 <b>Balance:</b> {coins} coins
🎁 <b>Gifts Received:</b> {gifts_received}
📤 <b>Gifts Sent:</b> {gifts_sent}

💡 <b>Tip:</b> Send messages to earn coins!
        """
        await message.reply_text(balance_text)
    except:
        pass

@app.on_message(filters.command("gifts", prefixes=["/", "!", "."]))
async def gift_list(_, message):
    try:
        text = "🎁 <b>Available Gifts:</b>\n\n"
        sorted_gifts = sorted(GIFTS.items(), key=lambda x: x[1]["cost"])
        
        for emoji, gift_info in sorted_gifts:
            text += f"{emoji} <b>{gift_info['name']}</b> - {gift_info['cost']} coins\n"
        
        text += "\n📝 <b>Usage:</b> /sendgift @username GiftEmoji"
        text += "\n💡 <b>Example:</b> /sendgift @john 🌹"
        
        await message.reply_text(text)
    except:
        pass

@app.on_message(filters.command("sendgift", prefixes=["/", "!", "."]))
async def send_gift(_, message):
    try:
        parts = message.text.split(" ")
        if len(parts) < 3:
            return await message.reply_text("❌ <b>Usage:</b> /sendgift @username GiftEmoji\n💡 <b>Example:</b> /sendgift @john 🌹")
        
        target = parts[1].replace("@", "")
        gift_emoji = parts[2]
        
        sender_id, sender_name = get_user_info(message)
        if not sender_id:
            return
        
        sender_data = await get_user_data(sender_id)
        
        if gift_emoji not in GIFTS:
            return await message.reply_text("❌ <b>Invalid gift!</b> Use /gifts to see available gifts.")
        
        gift_info = GIFTS[gift_emoji]
        cost = gift_info["cost"]
        
        if sender_data["coins"] < cost:
            return await message.reply_text(f"😢 <b>Insufficient coins!</b>\n💰 You need {cost} coins but have {sender_data['coins']} coins.")
        
        await users_collection.update_one(
            {"user_id": sender_id},
            {"$inc": {"coins": -cost, "total_gifts_sent": 1}}
        )
        
        gift_record = {
            "sender_id": sender_id,
            "sender_name": sender_name,
            "receiver_name": target,
            "receiver_id": None,
            "gift_name": gift_info["name"],
            "gift_emoji": gift_emoji,
            "cost": cost,
            "timestamp": "2025",
            "claimed": False
        }
        
        await gifts_collection.insert_one(gift_record)
        updated_sender = await get_user_data(sender_id)
        
        success_msg = f"""
🎉 <b>Gift Sent Successfully!</b>

{gift_emoji} <b>{sender_name}</b> sent <b>{gift_info['name']}</b> to <b>@{target}</b>!

💝 <b>Gift Details:</b>
• <b>Gift:</b> {gift_emoji} {gift_info['name']}
• <b>Cost:</b> {cost} coins
• <b>From:</b> {sender_name}
• <b>To:</b> @{target}

💰 <b>{sender_name}'s remaining coins:</b> {updated_sender['coins']}

💕 <i>Love is in the air!</i>
        """
        
        await message.reply_text(success_msg)
    except:
        pass

async def claim_pending_gifts(user_id, username):
    try:
        pending_gifts = await gifts_collection.find({
            "receiver_name": username,
            "claimed": False
        }).to_list(length=None)
        
        if pending_gifts:
            total_bonus = 0
            gift_count = len(pending_gifts)
            
            for gift in pending_gifts:
                await gifts_collection.update_one(
                    {"_id": gift["_id"]},
                    {
                        "$set": {
                            "receiver_id": user_id,
                            "claimed": True
                        }
                    }
                )
                total_bonus += 5
            
            await users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"coins": total_bonus, "total_gifts_received": gift_count}}
            )
            
            return gift_count, total_bonus
        
        return 0, 0
    except:
        return 0, 0

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

HINGLISH_STORIES = [
    "Ek baar <b>{a}</b> aur <b>{b}</b> ek coffee shop me mile ☕. Garam coffee ke beech dono ki nazarein mili, aur kismat ne unki love story likh di ❤️✨",
    "Library me <b>{a}</b> aur <b>{b}</b> ne ek hi kitab uthane ke liye haath badhaya 📚. Unki ungliyan chhoo gayi, aur dil me ghanti baj gayi 💫💕",
    "Baarish ho rahi thi 🌧️ aur <b>{a}</b> bheeg raha tha. <b>{b}</b> ne chhatri aage badhayi ☂️. Ek chhatri ke neeche pyaar khil gaya 🌸",
    "Concert me 🎵 <b>{a}</b> aur <b>{b}</b> ek hi gaana gaa rahe the. Unki awaazein mili, aur dil bhi mil gaye 🎶❤️",
    "<b>{a}</b> naye shehar me kho gaya tha 🏙️ aur <b>{b}</b> ne rasta bataya. Saath chalte chalte unhe manzil bhi mili aur ek dusre ka saath bhi 💝",
    "Ek khoobsurat bagiche me 🌺 <b>{a}</b> gulaab dekh raha tha jab <b>{b}</b> saamne aaya. Bagicha aur bhi haseen ho gaya 🌹✨",
    "<b>{a}</b> ki kitaabein gir gayi 📖 aur <b>{b}</b> ne unhe uthaya. Us chhote se pal me dono ko lag gaya ki wo ek hi kahani padh rahe hain 💘",
    "Sunset ke waqt beach pe 🌅 <b>{a}</b> aur <b>{b}</b> ne ret ka ghar banaya 🏰. Par unke dilon ne usse bhi mazboot ghar bana liya 💞",
    "Park me <b>{a}</b> pakshiyon ko daana dal raha tha 🐦 aur <b>{b}</b> bhi daana lekar aa gayi. Chidiyon ke chehchahe me dono ki hansi bhi mil gayi 🎭💕",
    "Light chali gayi 🕯️ aur <b>{a}</b> aur <b>{b}</b> ne mombatti ki roshni me raat bhar baatein ki. Andhere me unhe apni sabse roshan roshni mil gayi ✨❤️",
    "<b>{a}</b> sunset ki painting bana raha tha 🎨. <b>{b}</b> ne kaha 'Kitni sundar hai'. <b>{a}</b> ne muskura ke kaha, 'Tumse zyada nahi' 😍💝",
    "Dance class me 💃 <b>{a}</b> ke dono pair ulte pad rahe the, par <b>{b}</b> ne bade pyaar se sikhaya. Naachte naachte dono ek dusre ke dil me utar gaye 🕺❤️",
    "<b>{a}</b> ne ek billi ke bachche ko bachaya 🐱 aur <b>{b}</b> ne use ghar dilwaya. Billi ko ghar mila, aur dono ko ek dusre ke saath apna ghar 🏠💕",
    "Cooking class me 👨‍🍳 <b>{a}</b> ne khaana jala diya, par <b>{b}</b> bola ki isme pyaar ka swaad hai. Kabhi kabhi sabse achhi recipe dil se banti hai 💝🍳",
    "<b>{a}</b> aur <b>{b}</b> dono aakhri chocolate lene gaye 🍫. Dono ne baant liya, aur dheere dheere poori zindagi baantne ka irada bhi bana liya 💍✨",
    "Station pe 🚂 <b>{a}</b> train me chadhne hi wala tha jab <b>{b}</b> bheed me daudte hue chillayi 'Ruko!' Tabhi dono ko pata chal gaya ki ye pyaar hai ❤️🏃",
    "<b>{a}</b> raat ko akele taare dekh raha tha 🌟. <b>{b}</b> telescope lekar aa gayi. Taaron ke beech dono ko pata chala ki sabse sundar taara unka saath hai 👫✨",
    "Baking me kitchen me aata bikhar gaya 🧁. <b>{a}</b> sharma gaya, par <b>{b}</b> hans padi aur saath lag gayi. Kabhi kabhi pyaar gandha hota hai, par hamesha meetha 💕👫",
    "<b>{a}</b> ne brahmaand ko khat likha 📝 ki use sachcha pyaar chahiye. <b>{b}</b> ko wo khat mila aur wo har dua ka jawab ban gayi 🙏💝",
    "Sabzi mandi me 🍎 <b>{a}</b> aur <b>{b}</b> dono ne aakhri seb uthana chaha. Dono ne baant liya, aur zindagi bhar ki meethas bhi 🍯❤️",
    'College ki canteen me 🍜 <b>{a}</b> ke paas paise kam pad gaye. <b>{b}</b> ne chupke se bill bhar diya. Us din ke baad canteen ki chai me alag hi meethas thi ☕💕',
    'Bus me khidki wali seat ke liye 🚌 <b>{a}</b> aur <b>{b}</b> ki bahas ho gayi. Aadhe ghante baad dono ek dusre ka phone number maang rahe the 📱❤️',
    'Diwali ki raat 🪔 <b>{a}</b> diye jala raha tha aur <b>{b}</b> rangoli bana rahi thi. Diyon ki roshni me dono ke chehre aur bhi chamak uthe ✨💞',
    'Holi me 🎨 <b>{a}</b> ne <b>{b}</b> ko gulal laga diya. Rang utar gaya, par dil pe laga rang kabhi nahi utra 💖',
    'Train ki lambi yatra me 🚆 <b>{a}</b> aur <b>{b}</b> ne ek hi chai share ki. Station aate aate dono ek dusre ke ho chuke the ☕❤️',
    '<b>{a}</b> ka phone galti se <b>{b}</b> ko lag gaya 📞. Wrong number tha, par baatein itni achhi hui ki roz call aane lage 💕',
    'Mela me 🎡 <b>{a}</b> aur <b>{b}</b> ek hi jhoole me baith gaye. Jhoole ki unchai se zyada unke dil ki dhadkan badh rahi thi 💓',
    'Pani puri ke thele pe 🥘 <b>{a}</b> aur <b>{b}</b> dono ko teekha chahiye tha. Teekhe ke saath saath pyaar ka swaad bhi mil gaya 🔥❤️',
    '<b>{a}</b> exam ki tension me tha 📚 aur <b>{b}</b> ne notes de diye. Result se zyada khushi us muskurahat ki thi jo <b>{b}</b> ne di 😊💕',
    'Monsoon me chai ke saath pakode 🌧️ <b>{a}</b> bana raha tha aur <b>{b}</b> kha rahi thi. Chai thandi ho gayi par baatein garam rahi ☕💞',
    'Shaadi me 💒 <b>{a}</b> aur <b>{b}</b> ek hi table pe baithe the. Doosron ki shaadi me dono ko apna future dikhne laga 💍✨',
    '<b>{a}</b> ne gaana gaya 🎤 aur <b>{b}</b> ne taaliyan bajayi. Ek taali ne hi dil jeet liya 🎶❤️',
    'Cinema hall me 🎬 <b>{a}</b> aur <b>{b}</b> ne popcorn ek hi dibbe se uthaya. Film khatam ho gayi par kahani abhi shuru hui thi 🍿💕',
    'Raat ko chhat pe 🌙 <b>{a}</b> chand dekh raha tha aur <b>{b}</b> bhi wahi aa gayi. Chand ne bas muskura ke dono ko ek kar diya ✨❤️',
    '<b>{a}</b> ne cycle ki race jeeti 🚲 aur <b>{b}</b> sabse zor se taaliyan baja rahi thi. Medal se zyada wo taaliyan yaad rahi 🏅💞',
    'Gaon ke mele me 🎪 <b>{a}</b> ne <b>{b}</b> ke liye ek chhota sa gudda jeeta. Wo gudda aaj bhi unke ghar ki shaan hai 🧸💕',
    'Shaam ki aarti me 🙏 <b>{a}</b> aur <b>{b}</b> ne ek saath haath jode. Dono ne ek hi dua maangi, aur wo dua poori ho gayi ❤️',
    '<b>{a}</b> ne apni diary me ek naam likha tha 📝. Ek din <b>{b}</b> ne wo diary padhi aur samajh gayi ki wo naam uska hi tha 💘',
    'Metro me bheed thi 🚇 aur <b>{a}</b> ne <b>{b}</b> ko apni seat de di. Ek seat ne unhe zindagi bhar ka saath de diya 💕',
    '<b>{a}</b> aur <b>{b}</b> ne ek saath pehli baar golgappe khaaye 😋. Pani teekha tha, par pyaar usse bhi zyada meetha nikla 💞',
    'Library band hone wali thi 📖 aur <b>{a}</b> aur <b>{b}</b> dono akhiri page padh rahe the. Kitab khatam hui, par unki kahani abhi baaki thi ✨❤️',
    'Aandhi me <b>{a}</b> ka dupatta/cap ud gaya 🌪️ aur <b>{b}</b> ne daud ke pakda. Bhagte bhagte dono ko apni manzil mil gayi 💝',
    '<b>{a}</b> ne apni maa se kaha ki ek ladki/ladka pasand hai 🥰. Maa ne poocha naam kya hai, aur <b>{b}</b> ka naam sunke maa bhi muskura di 💕',
    'Ek chhote se sheher ke cafe me 🌆 <b>{a}</b> roz ek hi seat pe baithta tha. Ek din wahan <b>{b}</b> aa gayi, aur seat ab do logon ki ho gayi ☕❤️',
    'Naye saal ki raat 🎆 <b>{a}</b> aur <b>{b}</b> ne ek saath countdown kiya. 12 bajte hi dono ne mann hi mann ek dusre ko maang liya ✨💞',
    '<b>{a}</b> ko tairna nahi aata tha 🏊 aur <b>{b}</b> ne sikhaya. Paani se darr gaya, par pyaar me dubne se nahi 💕',
    'Rakhi ke din bhi 🎀 <b>{a}</b> aur <b>{b}</b> ek dusre ko dekhte reh gaye. Dosti itni gehri thi ki dil ne use pyaar bana liya ❤️',
    "<b>{a}</b> ne <b>{b}</b> ko ek chhoti si chitthi likhi ✉️ jisme sirf itna tha: 'Tum meri sabse achhi aadat ho.' Jawab aaya: 'Aur tum meri sabse pyaari lat' 😄💘",
    'Rail ki patri ke paas 🌾 <b>{a}</b> aur <b>{b}</b> ne sunset dekha. Train gujar gayi, par wo shaam unke dil me thehar gayi 🌅💞',
    'Chhat pe patang udate hue 🪁 <b>{a}</b> ki dor <b>{b}</b> ki dor se uljh gayi. Patang kat gayi, par dono ke dil ek ho gaye ❤️',
    "Kabhi kabhi ek 'hi' hi kaafi hota hai 💬. <b>{a}</b> ne <b>{b}</b> ko sirf 'Hi' bheja, aur baatein subah tak chalti rahi 🌙💕",
    'Midnight me bhookh lagi 🍕 aur <b>{a}</b> ne <b>{b}</b> ko bulaya. Pizza ke saath dono ko ek dusre ka saath bhi pasand aa gaya 💖',
    '<b>{a}</b> ko naya shehar bilkul achha nahi lag raha tha 🏙️. Phir <b>{b}</b> mili aur wahi shehar ghar jaisa lagne laga 🏠❤️',
    'Holiday me pahadon pe ⛰️ <b>{a}</b> aur <b>{b}</b> ek hi tent me phans gaye. Thand me garam chai aur garam dil dono mil gaye ☕💞',
    '<b>{a}</b> ne <b>{b}</b> ko ek gulaab diya 🌹 aur kaha ki ye kaante wala nahi, sirf pyaar wala hai. <b>{b}</b> ne muskura ke le liya 💕',
    'Ek purane radio pe 📻 <b>{a}</b> aur <b>{b}</b> ko apna favourite gaana ek saath sunayi diya. Pyaar bhi aise hi achanak sunayi deta hai 🎶❤️',
    'Exam hall me 🏫 <b>{a}</b> ne pen nahi laya tha. <b>{b}</b> ne apna pen diya aur dono ke beech dosti ki shuruat ho gayi, jo baad me pyaar ban gayi ✒️💘',
    'Aaj ke zamane me bhi 📮 <b>{a}</b> ne <b>{b}</b> ko haath se chitthi likhi. Wo chitthi aaj bhi <b>{b}</b> ki kitab me sambhal ke rakhi hai 💌',
    'Pehli baarish me 🌦️ <b>{a}</b> ne <b>{b}</b> ke saath bheegne ka maza liya. Baarish ruki, par pyaar ki fuhaar chalti rahi 💞',
    '<b>{a}</b> ne <b>{b}</b> ke liye ek gaana likha 🎵. Bas do line thi, par <b>{b}</b> ne use apni ringtone bana liya 📱❤️',
    'Ek bheed bhare bazaar me 🛍️ <b>{a}</b> ka haath <b>{b}</b> ke haath se takra gaya. Dono ne sorry bola, aur phir ek saath chai pi 💕',
    "Dosti ke bahane <b>{a}</b> roz <b>{b}</b> ke ghar ke saamne se guzarta tha 🚶. Ek din <b>{b}</b> ne darwaze pe khade hokar bola, 'Aaj andar aa jao' 🏡💘",
    '<b>{a}</b> aur <b>{b}</b> ne ek saath apni pehli trip plan ki 🧳. Manzil se zyada mazaa raaste me aaya ✈️❤️',
    'Ghar ki chhat pe 🌃 <b>{a}</b> aur <b>{b}</b> ne raat bhar taare ginne ki koshish ki. Taare kam pad gaye, par baatein khatam nahi hui ✨💞',
    '<b>{a}</b> ka din bahut kharab tha 😔. <b>{b}</b> ne bina kuch bole ek garam chai aur ek jhappi de di. Sab theek ho gaya ☕🤗❤️',
    'Mandir ki seedhiyon pe 🛕 <b>{a}</b> ne ek jhumka/ek chhota sa tabeez <b>{b}</b> ko diya. Bhagwan ne un dono ki jodi pehle hi likh di thi 🙏💕',
    '<b>{a}</b> ne ek puzzle shuru kiya 🧩 aur <b>{b}</b> ne usme madad ki. Aakhri tukda jab laga, dono ko lagaa ki wo bhi ek puzzle ke do tukde the 💞',
    'Gharwalon se chhup ke 🤫 <b>{a}</b> aur <b>{b}</b> ne bike pe lambi ride li. Hawa me ud ti zulfon me bhi pyaar ki mahak thi 🏍️❤️',
    "<b>{a}</b> ko subah uthna pasand nahi tha 😴. Jab se <b>{b}</b> ne 'Good morning' bhejna shuru kiya, subah ka intezaar rehne laga 🌅💕",
    'Library ke ek kone me 📚 <b>{a}</b> aur <b>{b}</b> dono apni kitab me kam, ek dusre me zyada kho gaye the. Sabse romantic chapter wahi tha 💘',
    'Ek chhote se gaon ki gali me 🏘️ <b>{a}</b> ne <b>{b}</b> ko pehli baar dekha. Chhoti si gali, par pyaar ka bada sa aasman 🌈❤️',
    "<b>{a}</b> ne <b>{b}</b> se pucha, 'Chai peeyogi/peeyoge?' ☕ <b>{b}</b> ne kaha, 'Bas tumhare saath.' Aur chai ke saath poori zindagi ka plan ban gaya 💞",
    'Gaadi kharab ho gayi 🚗 aur <b>{a}</b> ko lift chahiye thi. <b>{b}</b> ruka, aur wo lift zindagi bhar ke safar me badal gayi 🛣️❤️',
    'Mobile ki battery khatam ho gayi 🔋 aur <b>{a}</b> <b>{b}</b> ke ghar ke bahar charger maangne pahunch gaya. Charger mila, aur dil bhi charge ho gaya 😄💕',
    '<b>{a}</b> ko pata hi nahi chala ki kab <b>{b}</b> uski sabse achhi dost se uski sabse zaroori insaan ban gayi 🤝💞',
    'Subah ki sair me 🌄 <b>{a}</b> aur <b>{b}</b> roz ek hi mod pe mil jaate the. Ek din dono ne bina bole ek saath chalna shuru kar diya 🚶\u200d♂️🚶\u200d♀️❤️',
    "<b>{a}</b> ne <b>{b}</b> ko ek rose-sa chhota sa phool diya 🌼 aur kaha 'Ye mere dil ka ek tukda hai.' <b>{b}</b> ne use dil se laga liya 💕",
    'Raat ki baarish me 🌧️ <b>{a}</b> ne apna jacket <b>{b}</b> ko de diya. Jacket garam tha, par us gesture ne dil ko aur bhi garam kar diya 🧥❤️',
    'Akeli shaam me 🌇 <b>{a}</b> ne ek gaana lagaya aur <b>{b}</b> ne usi gaane pe chupchap taal di. Dono ne ek dusre ko dekha aur muskura diye 🎧💞',
    "Pehli baar milne pe 🥰 <b>{a}</b> itna ghabra gaya ki apna naam hi bhool gaya. <b>{b}</b> hans padi aur bola, 'Chalo, main bata deti hoon, tumhara naam {a} hai' 😂💕",
]

HINGLISH_ENDINGS = [
    "\n\n💕 <i>Aur dono hamesha khushi khushi saath rahe...</i>",
    "\n\n❤️ <i>Sachcha pyaar apna rasta khud dhoondh leta hai...</i>",
    "\n\n💞 <i>Jise log poori zindagi dhoondhte hain, wo inhe ek dusre me mil gaya...</i>",
    "\n\n✨ <i>Is bheed bhari duniya me dono ko ek dusre me sukoon mil gaya...</i>",
    "\n\n💝 <i>Pyaar perfect insaan dhoondhna nahi, apne liye perfect insaan milna hai...</i>",
    "\n\n🌹 <i>Har love story khoobsurat hoti hai, par inki kahani sabse khaas thi...</i>",
]

HINGLISH_HEADERS = [
    "💕 <b>Love Story</b> 💕",
    "❤️ <b>Pyaar Ki Kahani</b> ❤️",
    "💞 <b>Dil Ki Baat</b> 💞",
    "✨ <b>Ishq Ka Afsana</b> ✨",
    "🌹 <b>Mohabbat Ki Dastaan</b> 🌹",
]


async def gemini_love_story(name1, name2):
    """Gemini se Hinglish story banwao. Fail ho to None."""
    if not GEMINI_API_KEY:
        return None
    prompt = (
        f"{name1} aur {name2} ki ek chhoti, pyaari aur romantic love story likho. "
        "Language Hinglish honi chahiye (Roman script me Hindi aur English ka mix, jaise doston ke beech baat hoti hai). "
        "4 se 6 chhote vaakya, 3 se 5 emojis, kahani har baar nayi aur alag ho. "
        "Story family friendly ho, koi gaali ya adult baat nahi. "
        "Aakhri line ek meethi si seekh ya dua jaisi ho. "
        "Sirf story likho, koi heading, bullet ya extra explanation nahi."
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 1.0, "maxOutputTokens": 600},
    }
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    try:
        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    print(f"[Gemini] status {resp.status}: {(await resp.text())[:200]}")
                    return None
                data = await resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if not text:
            return None
        return html.escape(text)
    except Exception as e:
        print(f"[Gemini] error: {type(e).__name__}: {e}")
        return None


@app.on_message(filters.command("story", prefixes=["/", "!", "."]))
async def love_story(_, message):
    try:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            return await message.reply_text(
                "❌ <b>Aise use karo:</b> /story Naam1 Naam2\n💡 <b>Example:</b> /story Raj Priya"
            )

        name1 = html.escape(parts[1].strip())
        name2 = html.escape(parts[2].strip())

        wait = None
        if GEMINI_API_KEY:
            wait = await message.reply_text("✍️ Kahani likh raha hoon...")

        ai_story = await gemini_love_story(name1, name2)
        if ai_story:
            story = f"{ai_story}"
        else:
            story = random.choice(HINGLISH_STORIES).format(a=name1, b=name2)
            story += random.choice(HINGLISH_ENDINGS)

        final_story = f"{random.choice(HINGLISH_HEADERS)}\n\n{story}"
        if wait:
            try:
                await wait.edit_text(final_story)
            except Exception:
                await message.reply_text(final_story)
        else:
            await message.reply_text(final_story)

        uid, _ = get_user_info(message)
        if uid:
            await update_user_coins(uid, 5)
    except Exception as e:
        print(f"[story] error: {type(e).__name__}: {e}")

@app.on_message(filters.command(["mygifts", "received"], prefixes=["/", "!", "."]))
async def my_gifts(_, message):
    try:
        uid, username = get_user_info(message)
        if not uid:
            return
        
        await get_user_data(uid)
        
        gifts_received = await gifts_collection.find({"receiver_id": uid}).to_list(length=10)
        
        if not gifts_received:
            await message.reply_text(f"📭 <b>{username}</b>, you haven't received any gifts yet!\n💡 Ask someone to send you gifts using /sendgift")
            return
        
        gifts_text = f"🎁 <b>{username}'s Received Gifts:</b>\n\n"
        
        for i, gift in enumerate(gifts_received, 1):
            gifts_text += f"{i}. {gift['gift_emoji']} <b>{gift['gift_name']}</b> from <b>{gift['sender_name']}</b>\n"
        
        total_gifts = await gifts_collection.count_documents({"receiver_id": uid})
        gifts_text += f"\n💝 <b>Total gifts received:</b> {total_gifts}"
        
        await message.reply_text(gifts_text)
    except:
        pass

@app.on_message(filters.command(["top", "leaderboard"], prefixes=["/", "!", "."]))
async def leaderboard(_, message):
    try:
        top_users = await users_collection.find().sort("coins", -1).limit(10).to_list(length=10)
        
        if not top_users:
            await message.reply_text("📊 No users found in leaderboard!")
            return
        
        leaderboard_text = "🏆 <b>Top 10 Richest Users</b>\n\n"
        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        
        for i, user in enumerate(top_users):
            medal = medals[i] if i < len(medals) else "🏅"
            leaderboard_text += f"{medal} <b>User {user['user_id']}</b> - {user['coins']} coins\n"
        
        await message.reply_text(leaderboard_text)
    except:
        pass

@app.on_message(filters.text & ~filters.regex(r"^[/!.\-]"))
async def give_coins_and_claim_gifts(_, message):
    try:
        uid, username = get_user_info(message)
        if not uid:
            return
        
        await get_user_data(uid)
        
        gift_count, bonus_coins = await claim_pending_gifts(uid, username)
        
        if gift_count > 0:
            claim_msg = f"""
🎁 <b>Gifts Claimed!</b>

<b>{username}</b>, you received <b>{gift_count}</b> pending gifts!
💰 <b>Bonus coins earned:</b> {bonus_coins} coins

Use /mygifts to see your received gifts! 💝
            """
            await message.reply_text(claim_msg)
        
        if random.randint(1, 100) <= 20:
            await update_user_coins(uid, 1)
    except:
        pass
