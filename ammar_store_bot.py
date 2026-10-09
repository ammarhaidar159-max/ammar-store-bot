from flask import Flask
import threading
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Ammar Store Bot is Alive! ✅"
def run_flask():
    import os
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_flask, daemon=True).start()

import os, json, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = -1004405014166
SUPPORT_USER = 'store_spo'
APP_USER = 'store_spo'
WEB_USER = 'ammar_al3'
SHAM_CASH_CODE = '8f489621d0eceac3b4f0f989f2551b21'
USDT_ADDRESS = '0x5380A7e251Cc81DACB996d90BAa82145d6e8F91B'
EXCHANGE_RATE = 140
BALANCE_FILE = 'balances.json'
logging.basicConfig(level=logging.INFO)
PRODUCTS = {
    'pubg': {'name': '🎮 ببجي موبايل','items': [{'id': 'pubg_60','name': '60 شدة','price_usd': 1,'price_syp': 140},{'id': 'pubg_325','name': '325 شدة','price_usd': 5,'price_syp': 700},{'id': 'pubg_660','name': '660 شدة','price_usd': 10,'price_syp': 1400},{'id': 'pubg_1800','name': '1800 شدة','price_usd': 25,'price_syp': 3500},]},
    'freefire': {'name': '🔥 فري فاير','items': [{'id': 'ff_110','name': '110 جوهرة','price_usd': 1,'price_syp': 140},{'id': 'ff_230','name': '230 جوهرة','price_usd': 2,'price_syp': 280},{'id': 'ff_580','name': '580 جوهرة','price_usd': 5,'price_syp': 700},]}
}
user_states = {}
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path,'r',encoding='utf-8') as f: return json.load(f)
        except: return default
    return default
def save_json(path, data):
    with open(path,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
def get_balance(user_id):
    balances = load_json(BALANCE_FILE,{})
    uid=str(user_id)
    if uid not in balances: balances[uid]={'usd':0,'syp':0}
    return balances[uid], balances
def add_balance(user_id, amount, currency):
    balances=load_json(BALANCE_FILE,{})
    uid=str(user_id)
    if uid not in balances: balances[uid]={'usd':0,'syp':0}
    if currency=='usd': balances[uid]['usd']+=amount
    else: balances[uid]['syp']+=amount
    save_json(BALANCE_FILE,balances)
def deduct_balance(user_id, price_usd, price_syp):
    balances=load_json(BALANCE_FILE,{})
    uid=str(user_id)
    b=balances.get(uid,{'usd':0,'syp':0})
    if b['usd']>=price_usd:
        b['usd']-=price_usd; balances[uid]=b; save_json(BALANCE_FILE,balances); return True,'usd'
    elif b['syp']>=price_syp:
        b['syp']-=price_syp; balances[uid]=b; save_json(BALANCE_FILE,balances); return True,'syp'
    else:
        total=b['syp']+b['usd']*EXCHANGE_RATE
        if total>=price_syp:
            rem=price_syp
            if b['syp']>=rem: b['syp']-=rem; rem=0
            else: rem-=b['syp']; b['syp']=0; b['usd']-=rem/EXCHANGE_RATE
            balances[uid]=b; save_json(BALANCE_FILE,balances); return True,'mixed'
        return False,None
def has_enough(user_id, price_usd, price_syp):
    b,_=get_balance(user_id); return b['syp']+b['usd']*EXCHANGE_RATE>=price_syp
def main_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton('🎮 ببجي',callback_data='cat_pubg'),InlineKeyboardButton('🔥 فري فاير',callback_data='cat_freefire')],[InlineKeyboardButton('💰 شحن الرصيد',callback_data='charge'),InlineKeyboardButton('💳 رصيدي',callback_data='my_balance')],[InlineKeyboardButton('📱 التطبيقات',callback_data='apps'),InlineKeyboardButton('🌐 تصميم بوتات ومواقع',callback_data='web')],[InlineKeyboardButton('📞 الدعم',callback_data='support')]])
def back_to_main(): return InlineKeyboardMarkup([[InlineKeyboardButton('🏠 القائمة الرئيسية',callback_data='main')]])
WELCOME='💎 Ammar Store 💎\n\nأهلا وسهلا فيك بمتجر عمار\n🎮 شحن ببجي وفري فاير\n💰 رصيد بالدولار والسوري\n⚡ تسليم سريع\n\nاختر من القائمة 👇'
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(WELCOME,reply_markup=main_menu())
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query=update.callback_query; await query.answer(); data=query.data; user_id=query.from_user.id
    if data=='main':
        user_states.pop(user_id,None); await query.edit_message_text(WELCOME,reply_markup=main_menu())
    elif data=='my_balance':
        b,_=get_balance(user_id); await query.edit_message_text(f"💳 رصيدك في البوت\n\n💵 دولار: {b['usd']:.2f} $\n💴 سوري: {b['syp']} ل.س\n\n💱 سعر الصرف: 1$ = {EXCHANGE_RATE} ل.س\n💰 إجمالي بالسوري: {b['syp']+b['usd']*EXCHANGE_RATE} ل.س",reply_markup=back_to_main())
    elif data.startswith('cat_'):
        cat=data.replace('cat_','')
        if cat in PRODUCTS:
            prod=PRODUCTS[cat]; kb=[]
            for it in prod['items']: kb.append([InlineKeyboardButton(f"{it['name']} - {it['price_usd']}$ / {it['price_syp']} ل.س",callback_data=f"buy_{it['id']}")])
            kb.append([InlineKeyboardButton('🏠 القائمة الرئيسية',callback_data='main')]); await query.edit_message_text(f"{prod['name']}\n\nاختر الباقة 👇",reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith('buy_'):
        item_id=data.replace('buy_',''); found=None
        for cat in PRODUCTS.values():
            for it in cat['items']:
                if it['id']==item_id: found=it; break
        if not found: return
        if not has_enough(user_id,found['price_usd'],found['price_syp']):
            b,_=get_balance(user_id); await query.edit_message_text(f"❌ رصيدك غير كافي\nسعر المنتج: {found['price_usd']}$ / {found['price_syp']} ل.س\nرصيدك: {b['usd']:.2f}$ و {b['syp']} ل.س\n\nيرجى شحن رصيدك",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('💰 شحن الرصيد',callback_data='charge')],[InlineKeyboardButton('🏠 القائمة',callback_data='main')]])); return
        user_states[user_id]={'step':'awaiting_game_id','item':found}; await query.edit_message_text(f"📦 {found['name']}\n💵 {found['price_usd']}$ / {found['price_syp']} ل.س\n\n✏️ أرسل ID حسابك في اللعبة الآن:",reply_markup=back_to_main())
    elif data=='charge':
        kb=[[InlineKeyboardButton('💳 شام كاش',callback_data='charge_sham')],[InlineKeyboardButton('💲 USDT BEP20',callback_data='charge_usdt')],[InlineKeyboardButton('🏠 القائمة',callback_data='main')]]; await query.edit_message_text('💰 اختر طريقة شحن الرصيد 👇',reply_markup=InlineKeyboardMarkup(kb))
    elif data=='charge_sham':
        user_states[user_id]={'step':'sham_amount'}; await query.edit_message_text(f"💳 شحن عن طريق شام كاش\n\n🔗 كود شام كاش:\n`{SHAM_CASH_CODE}`\n\n👆 اضغط على الكود لنسخه\n\n✏️ الآن أرسل قيمة الرصيد المرسل (مثال: 10$ أو 1400 ل.س)",reply_markup=back_to_main(),parse_mode='Markdown')
    elif data=='charge_usdt':
        user_states[user_id]={'step':'usdt_amount'}; await query.edit_message_text(f"💲 شحن عن طريق USDT BEP20\n\n🔗 عنوان الإيداع (BEP20):\n`{USDT_ADDRESS}`\n\n👆 اضغط للنسخ\n\n⚠️ لسنا مسؤولين عن أي عملية تحويل ليس على شبكة BEP20\n\n✏️ الآن أرسل قيمة الرصيد المرسل",reply_markup=back_to_main(),parse_mode='Markdown')
    elif data=='apps':
        await query.edit_message_text(f"📱 شحن التطبيقات\n\nتواصل مع الدعم للحصول على أفضل سعر للبرامج والتطبيقات أسعار جملة وتجار\nمتوفر شحن لأكثر من 5000 برنامج\n\n📞 الدعم: @{APP_USER}",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('📞 تواصل مع الدعم',url=f'https://t.me/{APP_USER}')],[InlineKeyboardButton('🏠 القائمة',callback_data='main')]]))
    elif data=='web':
        await query.edit_message_text(f"🌐 تصميم بوتات ومواقع الويب\n\nتواصل مع الإداري المسؤول عن إنشاء وتصميم مواقع الويب لتزويده بمعلومات عن موقعك أو بوتك الشخصي\n\n👨‍💻 المسؤول: @{WEB_USER}",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('👨‍💻 تواصل مع المسؤول',url=f'https://t.me/{WEB_USER}')],[InlineKeyboardButton('🏠 القائمة',callback_data='main')]]))
    elif data=='support':
        await query.edit_message_text(f"📞 مركز الدعم\n\n💎 Ammar Store\n\n📱 الدعم: @{SUPPORT_USER}\n⚡ رد سريع",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('📞 تواصل مع الدعم',url=f'https://t.me/{SUPPORT_USER}')],[InlineKeyboardButton('🏠 القائمة',callback_data='main')]]))
    elif data.startswith('accept_charge_'):
        try:
            parts=data.split('_'); uid=int(parts[2]); amount=float(parts[3]); currency=parts[4]; add_balance(uid,amount,currency)
            try: await context.bot.send_message(chat_id=uid,text=f"✅ تم قبول العملية وشحن محفظتك بقيمة {amount} {'$' if currency=='usd' else 'ل.س'} 💰")
            except: pass
            await query.edit_message_text(query.message.text+'\n\n✅ تم القبول وشحن الرصيد')
        except Exception as e: await query.edit_message_text(f'خطأ: {e}')
    elif data.startswith('reject_charge_'):
        try:
            uid=int(data.split('_')[2])
            try: await context.bot.send_message(chat_id=uid,text=f"❌ تم رفض عملية الشحن راجع الدعم للاستفسار @{SUPPORT_USER}")
            except: pass
            await query.edit_message_text(query.message.text+'\n\n❌ تم الرفض')
        except Exception as e: await query.edit_message_text(f'خطأ: {e}')
    elif data.startswith('accept_game_'):
        try:
            parts=data.split('_',3); uid=int(parts[2]); rest=parts[3]; item_id,game_id=rest.split('_',1)
            try: await context.bot.send_message(chat_id=uid,text=f"✅ تم شحن طلبك على ID: {game_id} بنجاح 🎮")
            except: pass
            await query.edit_message_text(query.message.text+'\n\n✅ تم الشحن')
        except Exception as e: await query.edit_message_text(f'خطأ: {e}')
    elif data.startswith('reject_game_'):
        try:
            uid=int(data.split('_')[2])
            try: await context.bot.send_message(chat_id=uid,text=f"❌ تم رفض طلب شحن اللعبة راجع الدعم @{SUPPORT_USER}")
            except: pass
            await query.edit_message_text(query.message.text+'\n\n❌ تم الرفض')
        except Exception as e: await query.edit_message_text(f'خطأ: {e}')
def parse_amount(text):
    t=text.lower().replace('ل.س','').replace('ليرة','').replace('$','').replace('دولار','').strip()
    try: amount=float(t.split()[0])
    except:
        try: amount=float(t)
        except: amount=0
    return (amount,'syp') if amount>=100 else (amount,'usd')
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id; text=update.message.text.strip(); state=user_states.get(user_id)
    if not state: await update.message.reply_text('👇 اختر من القائمة',reply_markup=main_menu()); return
    if state.get('step')=='awaiting_game_id':
        item=state['item']
        if not has_enough(user_id,item['price_usd'],item['price_syp']): await update.message.reply_text('❌ رصيدك غير كافي يرجى شحن رصيدك',reply_markup=main_menu()); user_states.pop(user_id,None); return
        ok,cur=deduct_balance(user_id,item['price_usd'],item['price_syp'])
        if not ok: await update.message.reply_text('❌ رصيدك غير كافي',reply_markup=main_menu()); user_states.pop(user_id,None); return
        user=update.effective_user; order_text=f"🎮 طلب شحن لعبة جديد\n\n👤 العميل: @{user.username or 'بدون يوزر'}\n🆔 ايدي تيليجرام: {user.id}\n📛 الاسم: {user.full_name}\n🎯 ايدي اللعبة: {text}\n\n📦 المنتج: {item['name']}\n💵 السعر: {item['price_usd']}$ / {item['price_syp']} ل.س\n\nيوزر: @{user.username or user.id}"
        kb=InlineKeyboardMarkup([[InlineKeyboardButton('✅ قبول وشحن',callback_data=f"accept_game_{user_id}_{item['id']}_{text}")],[InlineKeyboardButton('❌ رفض',callback_data=f"reject_game_{user_id}")]])
        try: await context.bot.send_message(chat_id=CHANNEL_ID,text=order_text,reply_markup=kb)
        except: pass
        await update.message.reply_text(f"✅ تم تسجيل طلبك بنجاح\n\n📦 {item['name']}\n🎯 ID: {text}\n💰 تم خصم {item['price_usd']}$ / {item['price_syp']} ل.س من رصيدك\n\nسيتم الشحن قريبا",reply_markup=main_menu()); user_states.pop(user_id,None)
    elif state.get('step')=='sham_amount':
        user_states[user_id]={'step':'sham_tx','amount_text':text}; await update.message.reply_text('✏️ الآن أدخل رقم عملية التحويل لشام كاش:')
    elif state.get('step')=='sham_tx':
        amount_text=state['amount_text']; tx_id=text; amount,currency=parse_amount(amount_text); user=update.effective_user
        order_text=f"💳 طلب شحن رصيد - شام كاش\n\n👤 العميل: @{user.username or 'بدون يوزر'}\n🆔 ايدي: {user.id}\n📛 الاسم: {user.full_name}\n\n💰 المبلغ: {amount_text}\n🔢 الكمية: {amount} {currency}\n🔗 رقم العملية: {tx_id}\n\nشام كاش: {SHAM_CASH_CODE}\n\nيوزر: @{user.username or user.id}"
        kb=InlineKeyboardMarkup([[InlineKeyboardButton('✅ قبول',callback_data=f"accept_charge_{user_id}_{amount}_{currency}")],[InlineKeyboardButton('❌ رفض',callback_data=f"reject_charge_{user_id}")]])
        try: await context.bot.send_message(chat_id=CHANNEL_ID,text=order_text,reply_markup=kb)
        except: pass
        await update.message.reply_text('✅ تم تسجيل طلبك ستصلك رسالة تتضمن التفاصيل',reply_markup=main_menu()); user_states.pop(user_id,None)
    elif state.get('step')=='usdt_amount':
        user_states[user_id]={'step':'usdt_screenshot','amount_text':text}; await update.message.reply_text('📸 الآن أرسل لقطة شاشة عن الإيداع بالمبلغ المرسل:')
    elif state.get('step')=='usdt_screenshot': await update.message.reply_text('📸 الرجاء إرسال صورة لقطة الشاشة')
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id; state=user_states.get(user_id)
    if not state or state.get('step')!='usdt_screenshot': return
    amount_text=state['amount_text']; amount,currency=parse_amount(amount_text); user=update.effective_user
    order_text=f"💲 طلب شحن رصيد - USDT BEP20\n\n👤 العميل: @{user.username or 'بدون يوزر'}\n🆔 ايدي: {user.id}\n📛 الاسم: {user.full_name}\n\n💰 المبلغ: {amount_text}\n🔢 الكمية: {amount} {currency}\n\n🔗 العنوان: {USDT_ADDRESS}\n⚠️ الشبكة: BEP20 فقط\n\nيوزر: @{user.username or user.id}"
    kb=InlineKeyboardMarkup([[InlineKeyboardButton('✅ قبول',callback_data=f"accept_charge_{user_id}_{amount}_{currency}")],[InlineKeyboardButton('❌ رفض',callback_data=f"reject_charge_{user_id}")]])
    try:
        photo=update.message.photo[-1].file_id; await context.bot.send_photo(chat_id=CHANNEL_ID,photo=photo,caption=order_text,reply_markup=kb)
    except: await context.bot.send_message(chat_id=CHANNEL_ID,text=order_text,reply_markup=kb)
    await update.message.reply_text('✅ تم تسجيل طلبك ستصلك رسالة تتضمن التفاصيل',reply_markup=main_menu()); user_states.pop(user_id,None)
def main():
    tg_app=Application.builder().token(BOT_TOKEN).build()
    tg_app.add_handler(CommandHandler('start',start))
    tg_app.add_handler(CallbackQueryHandler(handle_callback))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text))
    tg_app.add_handler(MessageHandler(filters.PHOTO,handle_photo))
    print('Ammar Store Bot Running...'); tg_app.run_polling()
if __name__=='__main__': main()
