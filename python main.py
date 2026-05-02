import os
import logging
import asyncio
from io import BytesIO
import numpy as np
import cv2
from PIL import Image
import barcode
from barcode.writer import ImageWriter
from pyzbar.pyzbar import decode
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# قراءة التوكن من متغيرات البيئة
TOKEN = os.environ.get("8767255327:AAFWQFrJSHvABSZUF2x_OYg9sUTzNKUar8Q")

if not TOKEN:
    print("="*50)
    print("❌ خطأ فادح: لم يتم العثور على التوكن!")
    print("="*50)
    print("🔧 الحل:")
    print("1. اذهب إلى إعدادات Render.com")
    print("2. أضف متغير بيئة جديد باسم BOT_TOKEN")
    print("3. ضع توكن البوت الخاص بك كقيمة")
    print("4. أعد النشر (Deploy)")
    print("="*50)
    exit(1)

# تفعيل التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def text_to_barcode_bytes(text: str) -> BytesIO:
    """تحويل النص إلى باركود"""
    barcode_class = barcode.get_barcode_class('code128')
    my_barcode = barcode_class(text, writer=ImageWriter())
    buffer = BytesIO()
    my_barcode.write(buffer)
    buffer.seek(0)
    return buffer

def decode_barcode_from_bytes(image_bytes: bytes):
    """قراءة الباركود من الصورة"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return None
    
    barcodes = decode(img)
    if not barcodes:
        return None
    
    results = []
    for barcode_obj in barcodes:
        data = barcode_obj.data.decode('utf-8')
        btype = barcode_obj.type
        results.append((data, btype))
    
    return results

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *بوت تحويل الكود ↔ باركود*\n\n"
        "/encode نص - تحويل نص إلى باركود\n"
        "/decode - قراءة باركود من صورة\n"
        "/help - مساعدة",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *كيفية الاستخدام:*\n\n"
        "*نص ← باركود:* `/encode النص`\n"
        "*باركود ← نص:* أرسل صورة تحتوي على باركود",
        parse_mode='Markdown'
    )

async def encode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ أدخل النص: `/encode ABC123`", parse_mode='Markdown')
        return
    
    text = ' '.join(context.args)
    await update.message.reply_text("🔄 جاري الإنشاء...")
    
    try:
        buffer = text_to_barcode_bytes(text)
        await update.message.reply_photo(
            photo=InputFile(buffer, filename="barcode.png"),
            caption=f"✅ النص: `{text}`",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

async def decode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ أرسل صورة تحتوي على باركود")
        return
    
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_data = await file.download_as_bytearray()
    
    await update.message.reply_text("🔄 جاري القراءة...")
    
    results = decode_barcode_from_bytes(image_data)
    
    if not results:
        await update.message.reply_text("❌ لم يتم العثور على باركود")
        return
    
    reply = f"✅ تم العثور على {len(results)} باركود:\n\n"
    for data, btype in results:
        reply += f"📦 النوع: `{btype}`\n🔢 البيانات: `{data}`\n\n"
    
    await update.message.reply_text(reply, parse_mode='Markdown')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await decode(update, context)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ أمر غير معروف. استخدم /help")

def main():
    print("="*40)
    print("🤖 بدء تشغيل بوت الباركود...")
    print(f"✅ التوكن: {TOKEN[:10]}... (تم التحقق)")
    print("="*40)
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("encode", encode))
    application.add_handler(CommandHandler("decode", decode))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    
    print("✅ البوت جاهز للعمل...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
