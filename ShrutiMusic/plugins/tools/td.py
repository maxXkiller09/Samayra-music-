# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com

import random

from pyrogram import filters

from ShrutiMusic import app

TRUTHS = [
    'Aaj tak ki sabse embarrassing cheez kya hui hai tumhare saath?',
    'Tumhara sabse bada darr kya hai?',
    'Kabhi kisi se jhooth bola hai jo abhi tak pakda nahi gaya?',
    'Is group me sabse zyada kisse baat karna pasand hai?',
    'Tumhara pehla crush kaun tha, aur kab?',
    'Phone me sabse last search kya kiya tha?',
    'Kabhi exam me cheating ki hai? Sach batao.',
    'Aisi kaun si aadat hai jo tum chhodna chahte ho par chhod nahi paate?',
    'Kisi ko bina bataye uska status ya story stalk ki hai?',
    'Tumhari life ka sabse bura din kaun sa tha?',
    'Agar ek din ke liye invisible ho jao to sabse pehle kya karoge?',
    'Aaj tak ka sabse bada jhooth kya bola hai apne ghar walon se?',
    'Kisi ka dil toda hai? Kaise?',
    'Tumhare phone ki gallery me sabse embarrassing photo kaun si hai?',
    'Raat ko akele me kaun sa gaana sunna pasand hai?',
    'Kabhi kisi dost ki chugli ki hai jo tumhe nahi karni chahiye thi?',
    'Tumhe apne andar sabse zyada kya pasand nahi hai?',
    'Kisi se sorry bolna tha par ego ki wajah se nahi bola?',
    'Agar tumhe ek superpower mil jaye to kaun si loge?',
    'Tumhari life ka sabse achha moment kaun sa raha hai?',
    'Kabhi class ya office me sote hue pakde gaye ho?',
    'Kisi ko propose kiya hai? Kya jawab mila?',
    'Tumhari sabse ajeeb habit kya hai?',
    'Dost ki kaun si baat tumhe sabse zyada irritate karti hai?',
    'Aaj tak ka sabse mehnga ya sabse bekar kharcha kya raha?',
    'Agar kal ka din tumhara aakhri din ho to kya karoge?',
    'Kaun sa secret hai jo tumne abhi tak kisi ko nahi bataya?',
    'Kabhi kisi se jaan boojh ke baat karna band kiya hai?',
    'Tumhare hisab se is group me sabse funny kaun hai?',
    'Apni life ka koi ek regret batao.',
    'Kabhi raat ko kisi ko bina wajah message karke delete kiya hai?',
    'Tumhe kis cheez ki sabse zyada tension rehti hai aajkal?',
    'Kaun sa jhooth tum sabse zyada bolte ho?',
    'Agar tumhe ek din ke liye kisi ke jaisa ban jana ho to kiske jaisa banoge?',
    'Kabhi kisi ke aage rona aa gaya ho? Kyun?',
    'Sabse ajeeb sapna kaun sa dekha hai?',
    'Phone ke bina ek poora din reh sakte ho? Sach batao.',
    'Kisi dost ke liye kabhi bahut bada sacrifice kiya hai?',
    'Pehli baar kab laga ki tum badi ho gaye ho?',
    'Is group me kisse sabse zyada trust karte ho?',
]

DARES = [
    'Apna sabse purana selfie is group me bhejo.',
    'Next 5 minute tak sirf emoji me baat karo.',
    'Group me kisi ek member ki taarif me 3 line likho.',
    'Apni awaaz me 10 second ka koi gaana gakar voice note bhejo.',
    'Apna wallpaper ya DP kisi funny photo se badlo, 10 minute ke liye.',
    "Group ke kisi ek member ko 'tum bahut cute ho' bolo.",
    'Apne phone ki gallery ka last photo bhejo.',
    '10 push-ups karo aur video ya proof bhejo.',
    "Apne kisi dost ko bina wajah 'I miss you' message karo.",
    "Next 10 minute tak apne naam ke aage 'Raja' ya 'Rani' lagao.",
    'Kisi ek Bollywood dialogue ko dramatic style me voice note me bolo.',
    'Apne last 3 searches batao.',
    'Ek chhoti si shayari likho, abhi, jisme kisi ek member ka naam ho.',
    'Apni sabse funny shakal banao aur selfie bhejo.',
    'Group ke sabse active member ko ek compliment do.',
    'Apne ghar ki khidki se bahar ka photo bhejo.',
    'Paani ka ek poora glass ek saans me pee ke dikhao.',
    'Apne favourite gaane ki ek line group me type karo.',
    'Apne kisi purane dost ko hello bolo jisse bahut din se baat nahi hui.',
    '30 second tak bina hase seedhe camera ko dekho, aur batao kitni der tak ruke.',
    'Kisi ek animal ki awaaz nikaal ke voice note bhejo.',
    "Apna current status 1 ghante ke liye 'Main sabse best hoon' rakho.",
    'Group me kisi ek member ko ek funny nickname do.',
    "Apne haath ki likhawat me 'Namaste' likh ke photo bhejo.",
    'Next 3 message sirf rhyming (tukbandi) me likho.',
    'Apne ek talent ka 10 second ka demo do.',
    'Group ke kisi member ke liye 2 line ka gaana banao.',
    "Mummy ya papa ko 'I love you' bolo aur unka reaction batao.",
    'Jis cheez se sabse zyada darr lagta hai uska naam likh ke bhejo.',
    'Apne jaise 3 emoji ka combo bhejo jo tumhari personality dikhaye.',
    'Group me sabko good night ya good morning aise bolo jaise news reader bolta hai.',
    'Ek minute me 5 achhi cheezein likho jo tumhare paas hain.',
    'Apni sabse pasandida selfie group me daalo.',
    'Aankhein band karke apna naam likh ke dikhao aur photo bhejo.',
    "Group ke kisi bhi ek member ko 1 minute ke liye 'Boss' bolo.",
    'Ek chhota sa joke sunao, jo sabko hasa de.',
    'Apne phone ki battery % aur screen time sach sach batao.',
    'Apne favourite khaane ka naam batao aur kisi ek member ko treat ka promise karo.',
    'Ek line me batao ki tum aaj kaisa feel kar rahe ho.',
    'Apne dost ke liye ek chhota sa thank you message bhejo.',
]


@app.on_message(filters.command("truth"))
async def get_truth(client, message):
    await message.reply_text(
        f"🎯 **Truth Question:**\n\n{random.choice(TRUTHS)}\n\n__Sach sach jawab dena!__"
    )


@app.on_message(filters.command("dare"))
async def get_dare(client, message):
    await message.reply_text(
        f"🔥 **Dare Challenge:**\n\n{random.choice(DARES)}\n\n__Himmat hai to karke dikhao!__"
    )


__HELP__ = """
**Truth ya Dare ke commands**

In commands se Truth ya Dare khelo:

- `/truth`: Ek random truth sawaal lo. Sach sach jawab dena!
- `/dare`: Ek random dare challenge lo. Himmat hai to poora karo!

**Example:**
- `/truth`: "Aaj tak ki sabse embarrassing cheez kya hui hai tumhare saath?"
- `/dare`: "10 push-ups karo aur proof bhejo."
"""

__MODULE__ = "Truth"
