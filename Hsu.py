import os
import io
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# مكتبات التوليد (النص -> باركود)
import qrcode
import barcode
from barcode.writer import ImageWriter

# مكتبات القراءة (صورة -> نص)
from PIL import Image
from pyzbar.pyzbar import decode

# إعدادات التسجيل (Logging) لمعرفة الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ضع التوكن الخاص ببوتك هنا من BotFather
TOKEN = "8753593662:AAGvzjd_UAs7yFW8tacXUScemNZqx88wCDc"

# أمر البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت الباركود العكسي!\n\n"
        "🔹 **لتحويل نص إلى QR Code:** أرسل النص مباشرة للبوت.\n"
        "🔹 **لقراءة باركود أو QR Code:** أرسل الصورة للبوت كـ (Photo)."
    )

# 1. تحويل النص إلى QR Code (أو باركود)
async def text_to_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_data = update.message.text
    
    # إشعار المستخدم بالمعالجة
    status_message = await update.message.reply_text("⏳ جاري توليد الـ QR Code...")

    try:
        # توليد QR Code بجودة عالية
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(text_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # حفظ الصورة في الذاكرة لإرسالها مباشرة دون تخزينها على الجهاز
        bio = io.BytesIO()
        bio.name = 'qrcode.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        
        # حذف رسالة الانتظار وإرسال الصورة
        await status_message.delete()
        await update.message.reply_photo(photo=bio, caption=f"✅ تم التوليد بنجاح للنص:\n`{text_data}`", parse_mode="Markdown")
        
    except Exception as e:
        await status_message.edit_text(f"❌ حدث خطأ أثناء التوليد: {str(e)}")

# 2. قراءة الصورة وعكسها إلى نص صحيح
async def code_to_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_message = await update.message.reply_text("🔍 جاري قراءة الصورة وفك التشفير...")
    
    try:
        # الحصول على أعلى جودة للصورة المرسلة
        photo_file = await update.message.photo[-1].get_file()
        
        # تحميل الصورة في الذاكرة
        photo_bytes = await photo_file.download_as_bytearray()
        img = Image.open(io.BytesIO(photo_bytes))
        
        # فك تشفير الباركود أو الـ QR Code
        decoded_objects = decode(img)
        
        if not decoded_objects:
            await status_message.edit_text("❌ لم يتم العثور على باركود أو QR Code واضح في هذه الصورة. يرجى التأكد من جودتها.")
            return
        
        # استخراج النصوص من الصورة (يدعم وجود أكثر من باركود في صورة واحدة)
        result_text = ""
        for obj in decoded_objects:
            data_type = obj.type  # نوع الباركود (QRCODE, EAN13, إلخ)
            data_str = obj.data.decode('utf-8')  # النص المستخرج
            result_text += f"🔹 **النوع:** {data_type}\n📝 **النص الأصلي:**\n`{data_str}`\n\n"
        
        await status_message.delete()
        await update.message.reply_text(f"✅ **تم العكس بنجاح:**\n\n{result_text}", parse_mode="Markdown")
        
    except Exception as e:
        await status_message.edit_text(f"❌ حدث خطأ أثناء قراءة الصورة: {str(e)}")

# تشغيل البوت
def main():
    # بناء التطبيق ومزامنتة مع التوكن
    app = Application.builder().token(TOKEN).build()
    
    # الحوالات (Handlers)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_code))
    app.add_handler(MessageHandler(filters.PHOTO, code_to_text))
    
    # بدء استقبال الرسائل
    print("⚡ البوت يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()

