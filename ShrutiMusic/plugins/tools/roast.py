import html
import os
import random

import aiohttp

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus

from ShrutiMusic import app
from ShrutiMusic.misc import SUDOERS

ROASTS = [
    "{m}, tumhara aura -1000 chal raha hai bro, positive karne ka tareeka 'touch grass' hai 🌱😭",
    "{m} bhai ka rizz itna low hai ki crush ne 'seen' karke bhi 'ick' de diya 💀",
    '{m}, tum NPC ho kya? Har baat pe wahi dialogue repeat karte ho 🤖',
    '{m}, tum itne delulu ho ki khud ki story me khud hi main character bana liya 🎬✨',
    '{m} ka confidence dekh ke lagta hai Wi-Fi password ke bina bhi 5G chal raha hai 😭📶',
    "{m}, bro tum wo ho jiske 'POV' reel pe sirf 3 views aate hain, aur 2 tumhare hi hote hain 📱💀",
    '{m}, tumhari personality mid hai, no cap 😭',
    "{m}, tum itne cooked ho ki gas bhi bol rahi hai 'bhai side ho ja' 🔥😂",
    '{m}, tumhare red flags itne hain ki bull bhi dar ke bhaag gaya 🚩🐂',
    '{m}, tum situationship me ho, aur situation tumhe notice bhi nahi karti 😭💔',
    '{m}, tumhari insta story pe sabse zyada views tumhare apne hain 👀📸',
    "{m}, tumhara 'sigma grindset' sirf alarm snooze karne tak chalta hai ⏰😴",
    "{m}, tum itne brainrot ho ki sapne me bhi 'skibidi' sunayi deta hai 🧠💀",
    "{m}, tumhara 'ghost' karne ka talent itna strong hai ki bhoot bhi tumse seekhna chahta hai 👻",
    "{m} ka main character energy: background me khada rehke bhi 'extra' lagta hai 😭🎭",
    "{m}, tum wo ho jo 'ratio' maang ke khud hi ratio ho jaata hai 📉💀",
    '{m}, tumhari vibe check fail ho gayi, ab re-attempt ke liye 3 mahine ruk 📝😭',
    '{m}, tum itne sus ho ki Among Us wale bhi tumhe vote kar dete hain 🔴😂',
    "{m}, bro 'lowkey' bol ke highkey sab kuch bata deta hai, secrets bhi 🤫💀",
    "{m}, tumhara 'skill issue' itna bada hai ki tutorial bhi tumse haar gaya 🎮😭",
    "{m}, tum wo ho jo 'bestie' bolke 3 minute me block kar deta hai 😭🚫",
    "{m}, tumhari 'glow up' ki journey abhi 'loading...' pe atki hai 🔄✨",
    "{m}, tum itne L ho ki Elo bhi 'negative' dikha raha hai 📉",
    "{m}, tum story pe 'close friends' daalke bhi sirf apni mummy ko dikhate ho 😂💚",
    "{m}, tumhare 'swag' ko dekh ke swag bhi apna naam badalna chahta hai 😎💀",
    "{m}, tumhari dating app me matches se zyada 'unmatch' hain 💔📱",
    '{m}, tum itne cringe ho ki cringe ko bhi cringe lagta hai 😬😭',
    "{m}, bro 'aura farming' kar raha hai, par zameen hi banjar nikli 🌾💀",
    "{m}, tum wo ho jo 'fit check' me sirf pajama dikhata hai 👕😂",
    "{m}, tumhari 'toxic trait' ye hai ki tum khud ko toxic nahi maante 🧪😭",
    "{m}, tum 'situation' ko 'relationship' samajh ke ghoom rahe ho, bro 😭💍",
    "{m}, tumhara 'no cap' bolna hi sabse bada cap hai 🧢😂",
    "{m}, tum itne slay ho ki slay bhi bola 'bhai mujhe chhod de' 💅😭",
    "{m}, tumhare comments dekh ke 'delete' button khud ro padta hai 🗑️😂",
    "{m}, tum 'rizzler' ho, par rizz ki jagah sirf 'hi' type karte ho 💬💀",
    "{m}, tumhara 'attitude' itna hai ki ghar me kutta bhi ignore karta hai 🐶😂",
    "{m}, tum 'pick me' energy me itne deep ho ki ab ghar ka rasta bhool gaye ho 🙋\u200d♂️💀",
    "{m}, tum 'aesthetic' bolke bas filter laga ke picture daalte ho 🎞️😭",
    "{m}, tumhara 'vibe' check karne gaye to bas 'buffering' dikha 🔄😭",
    "{m}, tum itne 'chill' ho ki fridge bhi tumse jalta hai ❄️😎",
    "{m}, tumhare 'standards' itne high hain ki WiFi bhi nahi pakad pata 📡😂",
    "{m}, tum 'overthinker' ho ya 'under-doer'? Dono me gold medal milta hai 🥇😭",
    "{m}, tum wo ho jo 'bro trust me' bolke sabse pehle fail hota hai 😭📉",
    "{m}, tumhari 'self-love' journey itni lambi hai ki mirror bhi thak gaya 🪞😂",
    "{m}, tum 'minimalist' ho? Haan, kyunki tumhare paas sirf 'excuses' hain 📦💀",
    "{m}, tum 'main character' ho, par script abhi tak 'draft' me hai 📝😭",
    "{m}, tum itne 'dry' reply karte ho ki Sahara bhi sharma jaye 🏜️💀",
    "{m}, tumhari 'stories' me sirf 'quotes' hain, aur wo bhi copy-paste 📋😂",
    "{m}, tum 'baddie' ho? Pehle apna 'bad' wala part to dikhao 💀✨",
    "{m}, tumhari 'reels' ki quality dekh ke Insta bhi 'report' karna chahta hai 📱😭",
    "{m}, tum 'mood' ho ya 'moody'? Dono confusion me hain 🎭😂",
    "{m}, tum itne 'broke' ho ki piggy bank bhi bola 'bhai udhaar do' 🐷💸",
    "{m}, tum 'situationship' ke 'ex' ho gaye, aur abhi tak 'situation' ka naam nahi pata 💔😭",
    "{m}, tumhari 'energy' 1% battery jaisi hai, charger dhoondhte reh jaoge 🔋💀",
    "{m}, tum 'adulting' me itne weak ho ki chai banane me bhi 'help' maangte ho ☕😭",
    "{m}, tum 'FOMO' me itne ho ki khaana bhi 'story' ke liye order karte ho 🍕📱",
    "{m}, tumhare 'sticker' dekh ke lagta hai tumhara emotional range 3 emojis hai 😂😭🙏",
    "{m}, tum 'late reply' ke king ho, aur reply bhi 'k' hi hota hai 👑📱",
    "{m}, tum 'attention seeker' ho ya 'attention-deficit'? Dono ko ek saath dekh liya 👀😂",
    "{m}, tum itne 'unbothered' ho ki bell baji to bhi 'kaun hai' ni bolte 🔔😎",
    "{m}, tum 'trend' follow karte ho, par ek din late 🕐😭",
    "{m}, tum 'gatekeep' karte ho, par kuch hai hi nahi gatekeep karne ko 🚪💀",
    "{m}, tum 'cancel culture' me ho? Pehle apna 'subscription' to cancel kar do 📺😂",
    "{m}, tumhare 'captions' itne deep hain ki poora Pacific Ocean sharma jaye 🌊😭",
    "{m}, tum 'ex' ko 'block' karke 'story' dekhne ke liye 'fake ID' banate ho 🕵️💀",
    "{m}, tum 'sleep schedule' ko 'sleep rumour' bana dete ho, kyunki hota hi nahi 😴😂",
    "{m}, tum 'rich' feel karte ho jab tak 'UPI' ka 'payment failed' na aaye 💳💀",
    "{m}, tum wo ho jo 'gym' jaake 'mirror selfie' leke 'home' wapas aata hai 🏋️📸",
    "{m}, tumhara 'bio' dekh ke lagta hai tumne 'ChatGPT' se 'cool' maanga tha 🤖😭",
    "{m}, tum 'sigma' ho? Phir 'group chat' me 'online' kyun ho 24x7? 💬😂",
    "{m}, tum 'chill guy' ho, par sirf tab tak jab tak 'wifi' chal raha ho 🛜😎",
    "{m}, tum 'moodboard' banate ho, par 'mood' hi 'blank' hai 🎨😭",
    "{m}, tumhara 'plot twist' ye hai ki tum 'plot' me the hi nahi 🎬💀",
    "{m}, tum 'gen z' ho ya 'gen zZz'? Neend pe poora control nahi 😴😂",
    "{m}, tum itne 'iconic' ho ki 'old photo' dekh ke bhi 'glow down' dikhta hai 📷💀",
    "{m}, tumhare 'memes' itne purane hain ki 'dinosaur' bhi 'ok boomer' bolta hai 🦖😭",
    "{m}, tum 'level up' karna chahte ho? Pehle 'level 1' me to aao 🎮😂",
    "{m}, tum 'rent free' mere dimaag me nahi, bas 'unpaid' ho 🧠💀",
    "{m}, tum 'giving' kya ho? 'Giving nothing' 😭✨",
    "{m}, tum 'ate' kar gaye ho? Haan, 'khaana' 🍛😂",
    "{m}, tum 'serving' ho? Haan, sirf 'cringe' 🍽️💀",
    "{m}, tum 'bussin' ho? Nahi, bas 'busy' dikhne ki acting karte ho 😎😭",
    "{m}, tumhara 'drip' dekh ke 'tap' bhi bola 'maine to band kar diya tha' 💧😂",
    "{m}, tum 'vibe' ho? Nahi, 'wifi' ke bina 'weak signal' ho 📶💀",
    "{m}, tumhari 'comeback' itni late hai ki 'argument' khatam ho chuka hai ⏳😭",
    "{m}, tum 'caught in 4K' ho, aur 'quality' bhi 144p ki hai 📹💀",
    "{m}, tumhara 'reply' itna slow hai ki 'typing...' dekh ke main so gaya 😴⌨️",
    "{m}, tum 'rizz god' ho? Pehle 'rizz' ki spelling to sahi karo 🔤😂",
    "{m}, tumhara 'pfp' dekh ke 'NPC' bhi bola 'ye mera bhai hai' 🖼️🤖",
    "{m}, tum 'bro' ho ya 'bruh'? Dono ek saath bol dete ho aur kuch nahi karte 💀",
    "{m}, tum 'reel' me 'trending audio' lagake bhi 'views' nahi laa paate 🎵📉",
    "{m}, tumhara 'followers' count dekh ke 'following' bhi sharma gaya 👥😭",
    "{m}, tum 'collab' maangte ho, par 'content' hi nahi hai 🤝💀",
    "{m}, tumhari 'consistency' itni strong hai ki 'ek din' ke baad 'break' le lete ho 📅😂",
    "{m}, tum 'bhai' ho? Haan, 'bhai' ki bhi 'kuch' ichha hoti hai 🙏😭",
    "{m}, tum 'content creator' ho? Haan, 'sirf' 'cringe' content 🎥💀",
    "{m}, tum 'minimal' text karte ho: 'k', 'hmm', 'ok' ✌️😂",
    "{m}, tum 'vibe' me ho ya 'vague' me? Ek baar 'clear' ho jao 🌫️😭",
    "{m}, tum 'mature' ho? Haan, 'cheese' ki tarah, 'smell' aati hai 🧀💀",
    "{m}, tumhara 'attitude' dekh ke 'ego' bhi bola 'bhai chill' 😤😂",
    "{m}, tum 'chai' pe 'discussion' karte ho, par 'chai' khatam hote hi 'topic' bhi 🍵💀",
    "{m}, tum 'full send' karte ho, par 'delivery' mein 'delay' hota hai 📦😭",
    "{m}, tumhara 'vibes' itna 'dull' hai ki 'filter' bhi 'fail' ho gaya 🎞️💀",
    "{m}, tum 'overconfident' ho, bilkul 'WiFi' ki tarah: 'full bars', 'no internet' 📶😂",
    "{m}, tum 'ghost' ho? Nahi, 'bhoot' bhi 'reply' karta hai 👻😭",
    "{m}, tum 'aesthetic' me 'beige' ho: 'boring' + 'flat' 🟫💀",
    "{m}, tum 'vibing' kar rahe ho? Nahi, 'buffering' kar rahe ho 🔄😂",
    "{m}, tum 'simp' ho? Haan, aur 'simp' bhi bola 'bhai khud ko dekh' 🥺💀",
    "{m}, tum 'villain arc' me ho, par 'hero' bhi 'confused' hai 🦹😭",
    "{m}, tum 'meme' ho? Haan, 'expired' meme 📉😂",
    "{m}, tum 'sassy' ho? Nahi, bas 'sauce' ka 'packet' ho, 'empty' 🍅💀",
    "{m}, tumhari 'attitude' wali 'story' pe '2 views' aaye, 'dono' tumhare 👀😭",
    "{m}, tum 'low-key' sab karte ho, par 'high-key' sab ko 'pata' hota hai 🔑😂",
    "{m}, tum 'reply' dene me 'professional' ho: '2 din' baad 'sorry bhai busy tha' 🕐💀",
    "{m}, tum 'game' ho? Haan, 'Flappy Bird' jaisa 'ek' baar 'viral', phir 'gone' 🐦😭",
    "{m}, tum 'streak' maintain karte ho? Haan, 'ghosting' ki 🔥👻",
    "{m}, tum 'story' me 'miss you' likhte ho, par 'DM' me 'hi' nahi bhejte 💌😂",
    "{m}, tumhara 'swag' itna 'fake' hai ki 'Temu' bhi bola 'maine nahi banaya' 🛒💀",
    "{m}, tumhara 'reel' dekh ke 'algorithm' bhi 'unfollow' kar gaya 🤖😭",
    "{m}, tum 'chill' ho? Nahi, bas 'tension' me 'chill' ki acting karte ho 🧊😂",
    "{m}, tum 'ek number' ho? Haan, bas 'ek' hi 'number' 'save' hai tumhare phone me 📞💀",
    "{m}, tum 'pro' ho? Haan, 'pro' 'procrastinator' ⏳😭",
    "{m}, tumhare 'dreams' bade hain, par 'alarm' chhote hain ⏰💀",
    "{m}, tumhara 'online' rehna 'offline' se zyada 'suspicious' hai 🟢👀",
    "{m}, tum itne cool ho ki roast bhi 'respect' se karna pad raha hai 🫡😂",
    "{m}, tumhara 'attitude' wapas 'start' ho jaye? Ya 'restart' karoge? 🔁😭",
    "{m}, bro tum 'cooked' nahi, tum to 'poora thali' ho 🍛💀",
]

SAVAGE_ROASTS = [
    '{m}, tumhara attitude itna bada hai, bas uske peeche kuch nahi hai 😌',
    '{m}, tum khud ko legend samajhte ho, par legend ke fans hote hain 💀',
    "{m}, tumhari 'main hi sabse best hoon' wali feeling ko koi 'review' nahi mila abhi tak ⭐",
    '{m}, tum itna bolte ho ki lagta hai silence tumhari sabse badi dushman hai 🤐',
    '{m}, tumhari baaton me wazan nahi, bas awaaz zyada hai 🔊',
    '{m}, tumhara swag dekh ke lagta hai discount pe mila hai 🏷️',
    '{m}, tum sabse smart ho, bas ye baat sirf tumhe pata hai 🧠',
    '{m}, tumhare opinions itne unwanted hain ki spam folder bhi block kar de 📧',
    "{m}, tumhari 'high value' wali baatein sirf tumhare status me high hain 📱",
    '{m}, tumhara ego itna bada hai ki usko khud ka alag Wi-Fi chahiye 📶',
    "{m}, tum jo bhi karte ho 'trend' ban jaata hai, ek hi insaan ke liye: tumhare liye 😌",
    '{m}, tumhari dhaak sirf group chat tak hai, real life me volume mute hota hai 🔇',
    "{m}, tumhara 'alpha' mindset aur mummy ke 'khana kha le' ke beech mukabla hamesha mummy jeetti hai 🍛",
    "{m}, tum jo 'level' dikhate ho, wo game ke beginner level se bhi neeche hai 🎮",
    "{m}, tumhari 'attitude' wali story pe sabse zyada reaction: 'bhai delete kar' 😂",
    '{m}, tum jitna sochte ho utne popular ho nahi, aur jitna popular dikhte ho utne ho nahi 😭',
    "{m}, tumhari 'main to kisi ki parwah nahi karta' wali line me hi sabse zyada parwah dikhti hai 👀",
    "{m}, tum sabko 'bhai' bolte ho, taaki koi tumhara naam na poochh sake 😂",
    "{m}, tumhari 'respect' mangne ki aadat dekh ke lagta hai pehle ye kamani padegi 💸",
    '{m}, tumhare kaam kam aur claims zyada hain, bilkul pending order jaise 📦',
    "{m}, tumhari 'main to seedha bol deta hoon' wali line ke peeche sirf 'bina soche' chhupa hai 🎯",
    "{m}, tum bahut 'real' ho, bas asli kuch nahi hai 😌",
    '{m}, tumhari baatein itni high level hain ki nichle log ko bhi samajh nahi aati, aur upar waale ko bhi nahi 🤷',
    "{m}, tumhara 'busy' hona sirf status me busy hai, calendar me khaali hai 📅",
    "{m}, tumhari tareef sirf tum karte ho, baaki sab 'achha hai bhai' bol ke nikal jaate hain 🙏",
    "{m}, tum jitni 'advice' dete ho, utna 'result' dikhate to aaj kuch aur hote 😂",
    "{m}, tumhare 'goals' itne bade hain ki unhe dekhne ke liye telescope chahiye 🔭",
    "{m}, tumhari 'hustle' sirf 'good morning' wali quote tak limited hai 🌅",
    "{m}, tum 'brand' ho? Haan, 'local' wala bhi nahi 😭",
    "{m}, tumhara 'swag' itna naqli hai ki asli swag bhi 'copyright' maang raha hai ©️",
    "{m}, tum 'king' ho? Haan, bas 'kingdom' ka pata nahi 👑😭",
    "{m}, tumhari 'main hi sahi hoon' wali aadat se lagta hai tumhe 'sorry' ka matlab hi nahi pata 😌",
    "{m}, tum 'class' dikhane aaye the, par 'attendance' bhi nahi laga paye 🏫",
    "{m}, tumhari 'ego' itni badi hai ki 'tum' uske saamne chhote lagte ho 😂",
    "{m}, tumhare 'standards' itne ooche hain ki khud bhi unhe chhoo nahi paate 🪜",
    "{m}, tum 'serious' ho? Haan, bas 'seriously' lene wala koi nahi 😭",
    "{m}, tumhara 'main kisi se kam nahi' wala confidence, aur 'result' ke beech ka gap bahut bada hai 📉",
    "{m}, tum 'leader' ho? Haan, 'follow' karne wale sirf 'bots' hain 🤖",
    "{m}, tumhari 'baat' me 'dum' hai? Haan, bas 'hawa' wala 💨",
    "{m}, tumhara 'attitude' aur 'reality' ke beech me 'network error' aa raha hai 📡",
    "{m}, tum 'khaas' ho, bas 'kaam' ke nahi 😌",
    "{m}, tumhari 'main hi sabse achha' wali baat ko 'ek vote' bhi nahi mila 🗳️",
    "{m}, tum 'influencer' ho? Haan, bas 'influence' kuch nahi 📱",
    "{m}, tumhari 'popularity' ka data abhi 'under review' hai, 2 saal se 🕐",
    "{m}, tum 'trend' bana rahe the, par 'trend' ne tumhe 'ignore' kar diya 📉",
    "{m}, tumhari 'dhaak' sirf 'online' chalti hai, 'offline' to 'mummy' ke saamne bhi nahi 😂",
    "{m}, tum 'bada' sochte ho, par 'chhota' kaam bhi 'adhura' rehta hai 🧩",
    "{m}, tumhari 'taiyari' itni hai ki 'result' ke din 'bahana' ready rehta hai 📝",
    "{m}, tum 'main character' ho, bas 'script' kisi ne nahi likhi 🎬",
    "{m}, tumhari 'baat' me 'logic' kam, 'drama' zyada hai, bilkul 'daily soap' jaisa 📺",
    "{m}, tum 'aage' badhna chahte ho, par 'peeche' wale 'excuses' kheench lete hain 🔙",
    "{m}, tumhare 'dost' tumse 'pyaar' karte hain, 'tumhari' 'baaton' se nahi 😂",
    "{m}, tumhari 'self-confidence' ka 'source' kya hai? 'Shishe' me 'khud ko dekhna'? 🪞",
    "{m}, tum 'rich' bante ho, par 'canteen' me 'udhaar' 'chalta' hai 💳",
    "{m}, tumhara 'nasha' kuch aur nahi, 'khud ki tareef' hai 🥴",
    "{m}, tum 'sach' bolte ho? Haan, bas 'kabhi kabhi' aur 'wo bhi galti se' 😂",
    "{m}, tumhari 'taqat' sirf 'type karne' me hai, 'kaam' karne me nahi ⌨️",
    "{m}, tum 'sabse alag' ho? Haan, bas 'sabke jaise' hi 🤷",
    "{m}, tumhari 'story' me 'attitude', 'reality' me 'latitude' bhi nahi 🗺️😂",
    "{m}, tum 'maalik' ho? Haan, bas 'khud ke' 'dimaag' ke bhi nahi 😭",
    "{m}, tumhari 'baatein' sunke lagta hai 'cut' aur 'paste' bhi tumse zyada 'original' hai ✂️",
    "{m}, tum 'sabse tez' ho? Haan, bas 'bahane' banane me 🏃",
    "{m}, tum jitna 'dikhte' ho, utna 'ho' jao to 'duniya' tumhari ho jayegi 🌍😌",
]


PUNS = [
    "{m}, tumhari 'light' hamesha 'gul' rehti hai, chahe ghar ho ya dimaag 💡",
    "{m}, tum itne 'cool' ho ki fridge bhi tumse 'tips' leta hai ❄️",
    "{m}, tumhari 'battery' aur 'patience' dono 5% pe chal rahi hain 🔋",
    "{m}, tum 'charge' me rehte ho, par kaam me 'discharge' ho jaate ho 🔌",
    "{m}, tumhara 'net' hamesha 'slow' aur 'bahane' hamesha 'fast' hote hain 📶",
    "{m}, tum 'sab kuch' sambhal lete ho, bas apna 'time' aur 'zubaan' chhod ke ⏰",
    "{m}, tumhari 'dum' sirf biryani me hai, baaki jagah 'dum' ki kami hai 🍛",
    "{m}, tum 'phone' utha lete ho, par 'zimmedari' kabhi nahi 📞",
    "{m}, tum 'raste' me ho, par manzil ka 'pata' tumhare 'GPS' ko bhi nahi 🗺️",
    "{m}, tumhari 'chai' me 'cheeni' kam hai ya tumhari 'baaton' me 'meethas'? Dono 'phiki' ☕",
    "{m}, tumhare 'plan' itne 'plain' hain ki kabhi 'plane' nahi pakadte ✈️",
    "{m}, tum 'stand' lete ho, par 'baithne' me ho 'champion' 🪑",
    "{m}, tum 'time' pe aate ho? Haan, 'time' ke 'baad' pe 🕐",
    "{m}, tum 'screen' pe 'busy' ho par 'life' me 'blank' 📱",
    "{m}, tum 'note' karte ho par 'yaad' kabhi nahi rakhte 📝",
    "{m}, tumhari 'maths' me 'hisaab' kam, 'bahane' zyada 🧮",
    "{m}, tum 'chalte' ho, par 'chalaki' me 'late' 🐢",
    "{m}, tumhara 'mood' 'swing' karta hai, par 'garden' me nahi, group me 🎢",
    "{m}, tum 'save' kuch nahi karte, sirf 'contact' aur 'excuses' 💾",
    "{m}, tumhari 'game' itni strong hai ki 'over' hone se pehle 'out' ho jaate ho 🏏",
    "{m}, tum 'bank' ke 'balance' jaise ho: 'dikhte' ho par 'milte' nahi 🏦",
    "{m}, tum 'door' pe 'knock' karte ho, par 'dimaag' ke 'door' band rakhte ho 🚪",
    "{m}, tum 'pen' to rakhte ho, par 'idea' ka 'refill' khatam 🖊️",
    "{m}, tumhari 'speed' dekh ke 'snail' bhi bola 'main aage nikalta hoon' 🐌",
    "{m}, tum 'fan' ho? Haan, par 'speed' sirf 'one' pe chalti hai 🌀",
    "{m}, tumhara 'sense' itna 'common' hai ki 'uncommon' ho gaya 🧠",
    "{m}, tum 'mirror' ke saamne 'confident', 'exam' ke saamne 'confused' 🪞",
    "{m}, tumhari 'signal' wali baatein 'network' ke bahar hain 📡",
    "{m}, tum 'card' ho? Haan, 'expired' wala 💳",
    "{m}, tum 'break' lete ho par 'work' kabhi 'start' hi nahi karte ☕",
    "{m}, tum 'watch' pehente ho par 'time' kabhi nahi dekhte ⌚",
    "{m}, tumhara 'focus' 'camera' jaisa hai: 'blur' hi 'blur' 📷",
    "{m}, tumhari 'file' me 'data' kam aur 'drama' zyada 🗂️",
    "{m}, tum 'cut' lagate ho par 'result' me 'paste' ho jaate ho ✂️",
    "{m}, tum 'steps' ginte ho, par 'step up' kabhi nahi karte 👟",
    "{m}, tumhari 'story' me 'twist' hai, bas 'plot' gayab 🎬",
    "{m}, tum 'bell' ho? Haan, sirf 'bajne' par 'jaage' 🔔",
    "{m}, tum 'light weight' ho, par 'baatein' bahut 'heavy' 🏋️",
    "{m}, tumhari 'tyre' me 'hawa' kam aur 'baaton' me 'hawa' zyada 🚗",
    "{m}, tum 'lock' ho? Haan, 'dimaag' ka lock 'jam' hai 🔒",
    "{m}, tum 'cheque' ho? 'Bounce' hote ho 😂",
    "{m}, tumhare 'ideas' 'fresh' hain, bas 'expiry date' ke baad 🥛",
    "{m}, tum 'zero' me 'hero' ho, 'hero' me 'zero' ⭕",
    "{m}, tumhara 'swag' 'online' hai, 'offline' me 'out of stock' 🛒",
    "{m}, tum 'raat' ko 'jaagte' ho aur 'din' me 'jaagte' ka 'natak' karte ho 🌙",
]


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()


async def gemini_roast(name, extra=""):
    """Gemini se Gen Z Hinglish roast. Fail ho to None."""
    if not GEMINI_API_KEY:
        return None
    context = f" Context (is insaan ke baare me): {extra}." if extra else ""
    prompt = (
        f"{name} ke liye ek mazedaar Gen Z style roast likho.{context} "
        "Language Hinglish (Roman script me Hindi aur English ka mix). "
        "2 se 3 chhote vaakya, Insta/reels wale slang (rizz, aura, NPC, cooked, delulu jaise) use karo, 1 se 3 emojis. "
        "Roast sirf uski aadat, attitude ya overconfidence pe ho. "
        "Kisi ki shakal, body, family, dharm, jaati, gender, ya kisi insecurity pe bilkul nahi. "
        "Koi gaali ya adult baat nahi. Sirf roast likho, koi heading ya explanation nahi."
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 1.1, "maxOutputTokens": 300},
    }
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    print(f"[Gemini roast] status {resp.status}: {(await resp.text())[:200]}")
                    return None
                data = await resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return html.escape(text) if text else None
    except Exception as e:
        print(f"[Gemini roast] {type(e).__name__}: {e}")
        return None


async def _is_admin(chat_id, user_id):
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


@app.on_message(filters.command(["roast", "gali", "savage", "pun", "airoast"], prefixes=["/", "."]) & filters.group)
async def roast_user(client, message):
    cmd = message.command[0].lower()
    sender = message.from_user
    if not sender:
        return

    if not (sender.id in SUDOERS or await _is_admin(message.chat.id, sender.id)):
        return await message.reply_text("❌ Ye command sirf group admins ke liye hai.")

    reply = message.reply_to_message
    if not reply or not reply.from_user:
        return await message.reply_text("↩️ Jisko roast karna hai uske message pe reply karke /roast likho.")

    target = reply.from_user
    me = await client.get_me()
    if target.id == me.id:
        return await message.reply_text("😎 Mujhe roast karoge? Pehle apni comedy sudharo.")
    if target.is_bot:
        return await message.reply_text("🤖 Bot ko roast karne ka koi mazaa nahi hai.")

    mention = f'<a href="tg://user?id={target.id}">{html.escape(target.first_name or "Dost")}</a>'
    if cmd == "airoast":
        extra = message.text.split(None, 1)[1].strip()[:120] if len(message.command) > 1 else ""
        ai = await gemini_roast(target.first_name or "Dost", extra)
        text = f"{mention}, {ai}" if ai else random.choice(ROASTS + SAVAGE_ROASTS).format(m=mention)
    else:
        if cmd == "savage":
            pool = SAVAGE_ROASTS
        elif cmd == "pun":
            pool = PUNS
        else:
            pool = ROASTS + SAVAGE_ROASTS
        text = random.choice(pool).format(m=mention)
    await reply.reply_text(text + "\n\n<i>(Bas masti hai, bura mat maanna bestie 😭)</i>")


__MODULE__ = "Rᴏᴀsᴛ"
__HELP__ = """
**Roast (masti wale commands):**

• `/roast`: Kisi ke message pe reply karke ye likho, bot usko ek Hinglish roast dega (sirf group admins).
• `/gali`: Wahi kaam karta hai, bas masti wale roast ke saath.
• `/pun`: Shabdon ke do matlab wale clean wordplay roast.
• `/airoast [aadat]`: Gemini se naya, personal Gen Z roast (key lagi ho to). Example: `/airoast late aata hai`.
• `/savage`: Thoda sharp, ego wala roast (sirf behaviour aur attitude pe, kisi ki shakal ya family pe nahi).

Ye sirf group me chalta hai, DM me nahi. Roast halke aur mazaak wale hain.
"""
