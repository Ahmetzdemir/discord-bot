import discord
from discord.ext import commands
import google.generativeai as genai
import random
import re
import yt_dlp
import requests
import json
import aiohttp

# Google Gemini API yapılandırması
genai.configure(api_key=GOOGLE_API_KEY)

# Discord bot ayarı
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Yanıt verilecek kanallar
OTO_YANIT_KANALLAR = []

# Anahtar kelime yanıtları
ANAHTAR_KELIME_YANITLARI = {
    "selam": ["Merhaba!", "Selam! Nasılsın?", "Hey! Hoş geldin!"],
    "nasılsın": ["İyiyim, teşekkürler!", "Harika! Sen nasılsın?", "Çalışıyorum, sen?"],
    "ne yapıyorsun": ["Seninle konuşuyorum :)", "Kod satırları arasında dolaşıyorum!", "Sana yanıt vermekle meşgulüm."],
    "günaydın": ["Günaydın! Harika bir gün seni bekliyor!", "Güneş gibi parlıyorsun!", "Bugün harika geçsin!"],
    "iyi geceler": ["İyi geceler, tatlı rüyalar!", "Uykun bol, kabusun hiç olmasın!", "Yarın görüşürüz!"],
    "teşekkürler": ["Rica ederim!", "Ne demek, her zaman!", "Yardımcı olabildiysem ne mutlu!"],
    "seni seviyorum": ["Ben de seni seviyorum 💖", "Aww, çok naziksin!", "Kalp kalbe karşı derler 😄"],
    "görüşürüz": ["Görüşmek üzere!", "Kendine iyi bak!", "Yakında tekrar konuşalım!"],
    "bot musun": ["Yok ya ben gizli bir ajanım... 😏", "Evet, ama kalbim var!", "Botum ama dost canlısıyım :)"],
    "neden çalışmıyorsun": ["Belki de uykum var 😴", "Bir hata olabilir, tekrar dener misin?", "Şu an biraz meşgulüm 😅"],
    "sıkıldım": ["Hadi birlikte oyun oynayalım!", "Sana bir fıkra anlatayım mı?", "Sıkılmak mı? Ben buradayım!"],
    "şaka yap": ["Geçen gün elektrikle konuştum, 'akım' oldu!", "Matematikçiye sormuşlar: 'Yalnız mısın?' Cevap: 'Sinüsle kosinüs var!'", "Bilgisayar çökmüş, neden? Çünkü 'Windows' açık kalmış! 😅"],
    "müzik öner": ["Lo-fi mi seversin yoksa rock mı?", "Bugünlük biraz jazz öneririm 🎷", "Hadi nostalji: Barış Manço - Gülpembe 💿"],
    "film öner": ["Inception tam senlik!", "Bugünlük komedi: The Grand Budapest Hotel!", "Biraz gerilim: Shutter Island nasıl?"]
}

# Ortak AI cevap fonksiyonu
async def ai_cevapla(channel, mesaj_metni):
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(mesaj_metni)
        yanit = response.text

        if len(yanit) <= 2000:
            await channel.send(yanit)
        else:
            parcalar = [yanit[i:i+1990] for i in range(0, len(yanit), 1990)]
            for i, parca in enumerate(parcalar):
                await channel.send(f"**Cevap {i+1}/{len(parcalar)}**\n{parca}")
    except Exception as e:
        await channel.send(f"Yanıt verirken bir hata oluştu: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı!')
    print(f'Bot {len(bot.guilds)} sunucuda aktif')
    await bot.change_presence(activity=discord.Game(name="!yardım için hazır"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Eğer bu kanal listeliyse veya özel değilse, otomatik cevaplara devam et
    if not OTO_YANIT_KANALLAR or message.channel.id in OTO_YANIT_KANALLAR:
        content_lower = message.content.lower()
        olasi_yanitlar = []

        for keyword, responses in ANAHTAR_KELIME_YANITLARI.items():
            if keyword in content_lower:
                olasi_yanitlar.extend(responses)

        if olasi_yanitlar:
            response = random.choice(olasi_yanitlar)
            await message.channel.send(response)
            # Komutsa aşağıda tekrar işlememesi için dönüş yap
            return

        if bot.user.mentioned_in(message) and not message.mention_everyone:
            user_message = re.sub(rf"<@!?{bot.user.id}>", "", message.content).strip()

            if not user_message:
                await message.channel.send(f"Merhaba {message.author.mention}! Nasıl yardımcı olabilirim?")
            else:
                await message.channel.send("Düşünüyorum... ⏳")
                await ai_cevapla(message.channel, user_message)
            return  # Burada da dönüş yap, yoksa tekrar işler

    # En sonda sadece komutlar işleniyor
    await bot.process_commands(message)
@bot.command()
async def merhaba(ctx):
    await ctx.send("Selam! Ben buradayım 😊")

@bot.command()
async def sor(ctx, *, soru):
    await ctx.send("Cevaplanıyor... ⏳")
    await ai_cevapla(ctx, soru)

@bot.command()
async def yardım(ctx):
    embed = discord.Embed(
        title="Bot Komutları",
        description="İşte kullanabileceğiniz komutlar:",
        color=discord.Color.blue()
    )
    embed.add_field(name="!merhaba", value="Bot size selam verir", inline=False)
    embed.add_field(name="!sor [soru]", value="Yapay zekaya soru sorun", inline=False)
    embed.add_field(name="@Bot [mesaj]", value="Botu etiketleyerek de soru sorabilirsiniz", inline=False)
    embed.set_footer(text="Daha fazla yardım için geliştiriciyle iletişime geçin")
    
    await ctx.send(embed=embed)

@bot.command()
async def çal(ctx, *, arama):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("Önce bir ses kanalına katılmalısın!")
        return

    kanal = ctx.author.voice.channel

    try:
        await kanal.connect()
    except discord.ClientException:
        pass  # Zaten bağlıysa görmezden gel

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{arama}", download=False)['entries'][0]
            url = info['url']
            title = info.get('title', 'Bilinmeyen Şarkı')

        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
        ctx.voice_client.stop()
        ctx.voice_client.play(source)

        await ctx.send(f"🎶 **{title}** çalınıyor!")
    except Exception as e:
        await ctx.send(f"Şarkı çalınırken bir hata oluştu: {e}")

@bot.command()
async def dur(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Şarkı durduruldu.")
    else:
        await ctx.send("Çalan bir şey yok.")

@bot.command()
async def çık(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Ses kanalından çıktım.")
    else:
        await ctx.send("Zaten bir ses kanalında değilim.")

def get_waifu():
    url = "https://api.waifu.pics/nsfw/waifu"
    response = requests.get(url)
    data = response.json()
    return data['url']

def get_neko():
    url = "https://api.waifu.pics/nsfw/neko"
    response = requests.get(url)
    data = response.json()
    return data['url']

def get_trap():
    url = "https://api.waifu.pics/nsfw/trap"
    response = requests.get(url)
    data = response.json()
    return data['url']

def get_blowjob():
    url = "https://api.waifu.pics/nsfw/blowjob"
    response = requests.get(url)
    data = response.json()
    return data['url']

# Kategorilere göre komutlar
@bot.command()
async def waifu(ctx):
    waifu_url = get_waifu()
    await ctx.send(waifu_url)

@bot.command()
async def neko(ctx):
    neko_url = get_neko()
    await ctx.send(neko_url)

@bot.command()
async def trap(ctx):
    trap_url = get_trap()
    await ctx.send(trap_url)

@bot.command()
async def blowjob(ctx):
    blowjob_url = get_blowjob()
    await ctx.send(blowjob_url)

@bot.command()
async def oyunsaatim(ctx):
    await ctx.send("Oyun saatlerin getiriliyor...")

    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        'key': STEAM_API_KEY,
        'steamid': STEAM_ID,
        'include_appinfo': 1,
        'format': 'json'
    }

    response = requests.get(url, params=params)
    data = response.json()

    if 'games' not in data['response']:
        await ctx.send("Oyun bilgileri alınamadı.")
        return

    games = data['response']['games']
    sorted_games = sorted(games, key=lambda x: x['playtime_forever'], reverse=True)[:5]

    msg = "**En çok oynadığın 5 oyun:**\n"
    for game in sorted_games:
        name = game['name']
        hours = game['playtime_forever'] // 60
        msg += f"🎮 {name} — {hours} saat\n"

    await ctx.send(msg)

@bot.command()
async def rule34(ctx, *, tag: str):
    if not ctx.channel.is_nsfw():
        return await ctx.send("❌ Bu komut sadece NSFW kanallarında kullanılabilir.")

    url = f"https://rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&limit=100&tags={tag}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return await ctx.send("Rule34 API şu anda ulaşılamıyor.")
            
            try:
                data = await response.json()

                if not data:
                    return await ctx.send(f"Etiket bulunamadı: **{tag}**")

                chosen = random.choice(data)
                image_url = chosen["file_url"]

                await ctx.send(image_url)

            except Exception as e:
                print("Hata:", e)
                await ctx.send("Bir hata oluştu, lütfen tekrar dene.")

@bot.command()
async def yardımcı(ctx):
    embed = discord.Embed(
        title="Bot Komutları",
        description="İşte kullanabileceğiniz komutlar:",
        color=discord.Color.blue()
    )
    embed.add_field(name="!merhaba", value="Bot size selam verir", inline=False)
    embed.add_field(name="!sor [soru]", value="Yapay zekaya soru sorun", inline=False)
    embed.add_field(name="@Bot [mesaj]", value="Botu etiketleyerek de soru sorabilirsiniz", inline=False)
    embed.add_field(name="!oyunsaatim", value="Steam'deki oyun saatlerini gösterecek", inline=False)

    embed.add_field(name="Ses Komutları:", value="🎶 Sesli komutlar hakkında bilgi", inline=False)
    embed.add_field(name="!çal [arama]", value="YouTube'dan bir şarkı arar ve ses kanalında çalar", inline=False)
    embed.add_field(name="!dur", value="Çalan şarkıyı durdurur", inline=False)
    embed.add_field(name="!çık", value="Bot ses kanalından çıkar", inline=False)

    embed.add_field(name="NSFW Komutları:", value="🔞 Bu komutlar, NSFW içeriklere yöneliktir", inline=False)
    embed.add_field(name="!waifu", value="Waifu görseli gönderir", inline=False)
    embed.add_field(name="!neko", value="Neko görseli gönderir", inline=False)
    embed.add_field(name="!trap", value="Trap görseli gönderir", inline=False)
    embed.add_field(name="!blowjob", value="Blowjob görseli gönderir", inline=False)
    
    embed.set_footer(text="Daha fazla yardım için geliştiriciyle iletişime geçin")
    
    await ctx.send(embed=embed)

bot.run(BOT_TOKEN)
