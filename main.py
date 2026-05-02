import os
import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import barcode
from barcode.writer import ImageWriter
from pyzbar.pyzbar import decode
import cv2
import numpy as np
import io

# ⚠️ ضع التوكن الخاص بك هنا ⚠️
TOKEN = "8767255327:AAFWQFrJSHvABSZUF2x_OYg9sUTzNKUar8Q"  # استبدل هذا بالتوكن الحقيقي

# تفعيل التسجيل للأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBarcodeBot:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رسالة الترحيب"""
        welcome_text = """
🤖 *مرحباً بك في بوت تحويل الكود ↔ باركود!*

🎯 *الأوامر المتاحة:*

📝 `/encode` + النص  
▫️ يحول النص إلى صورة باركود
▫️ مثال: `/encode 1234567890`

📖 `/decode`  
▫️ أرسل صورة باركود وسأقرأها لك

🆘 `/help` - عرض هذه المساعدة

🔹 يدعم أنواع: Code128, EAN13, EAN8
🔹 حجم الباركود مناسب للطباعة والمسح

_أرسل /encode متبوعاً بالنص الذي تريد تحويله_
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        help_text = """
📚 *كيفية الاستخدام:*

1️⃣ *نص ← باركود*
اكتب: `/encode النص الذي تريده`
مثال: `/encode HELLO123`

2️⃣ *باركود ← نص*
أرسل صورة تحتوي على باركود وسأقوم بقراءتها تلقائياً

💡 *نصائح:*
• استخدم Code128 للنصوص الطويلة أو التي تحتوي على أحرف
• تأكد من وضوح الصورة عند التحويل العكسي
• الصورة الناتجة بدقة عالية (300 نقطة/بوصة)
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    @staticmethod
    async def encode(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تحويل النص إلى باركود"""
        try:
            # الحصول على النص من الأمر
            if not context.args:
                await update.message.reply_text("❌ *خطأ:* الرجاء إدخال النص بعد الأمر `/encode`\nمثال: `/encode ABC123`", parse_mode='Markdown')
                return
            
            text = ' '.join(context.args)
            
            # إعلام المستخدم بالبدء
            processing_msg = await update.message.reply_text("🔄 *جاري إنشاء الباركود...*", parse_mode='Markdown')
            
            # إنشاء الباركود (نوع Code128 يدعم كل النصوص)
            barcode_class = barcode.get_barcode_class('code128')
            my_barcode = barcode_class(text, writer=ImageWriter())
            
            # حفظ الباركود في ذاكرة مؤقتة
            buffer = io.BytesIO()
            my_barcode.write(buffer)
            buffer.seek(0)
            
            # إرسال الصورة للمستخدم
            await update.message.reply_photo(
                photo=InputFile(buffer, filename=f"barcode_{text[:15]}.png"),
                caption=f"✅ *تم التحويل بنجاح!*\n📝 النص: `{text}`\n📦 النوع: Code128",
                parse_mode='Markdown'
            )
            
            # حذف رسالة "جاري المعالجة"
            await processing_msg.delete()
            
        except Exception as e:
            logger.error(f"خطأ في التشفير: {e}")
            await update.message.reply_text(f"❌ *حدث خطأ:* غير قادر على إنشاء الباركود.\nتأكد من أن النص لا يحتوي على أحرف غير مدعومة.", parse_mode='Markdown')

    @staticmethod
    async def decode(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """قراءة الباركود من الصورة"""
        try:
            # التأكد من وجود صورة
            photo = update.message.photo[-1]  # أفضل جودة
            file = await photo.get_file()
            
            # إعلام المستخدم
            await update.message.reply_text("🔄 *جاري قراءة الباركود...*", parse_mode='Markdown')
            
            # تحميل الصورة إلى ذاكرة مؤقتة
            image_data = await file.download_as_bytearray()
            
            # تحويل إلى مصفوفة numpy
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                await update.message.reply_text("❌ *خطأ:* لم أتمكن من قراءة الصورة. تأكد من إرسال صورة صالحة.", parse_mode='Markdown')
                return
            
            # قراءة الباركودات
            barcodes = decode(img)
            
            if not barcodes:
                await update.message.reply_text("🔍 *لم يتم العثور على باركود!*\nتأكد من أن الصورة تحتوي على باركود واضح ومضاء بشكل جيد.", parse_mode='Markdown')
                return
            
            # عرض النتائج
            results_text = f"✅ *تم العثور على {len(barcodes)} باركود:*\n\n"
            for i, barcode_obj in enumerate(barcodes, 1):
                barcode_data = barcode_obj.data.decode('utf-8')
                barcode_type = barcode_obj.type
                results_text += f"{i}. 📦 النوع: `{barcode_type}`\n   🔢 البيانات: `{barcode_data}`\n\n"
            
            await update.message.reply_text(results_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"خطأ في فك التشفير: {e}")
            await update.message.reply_text("❌ *حدث خطأ:* تعذر قراءة الباركود. حاول إرسال صورة أوضح.", parse_mode='Markdown')

    @staticmethod
    async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الصور المرسلة (بدون أمر decode)"""
        await TelegramBarcodeBot.decode(update, context)

def main():
    """تشغيل البوت"""
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", TelegramBarcodeBot.start))
    application.add_handler(CommandHandler("help", TelegramBarcodeBot.help_command))
    application.add_handler(CommandHandler("encode", TelegramBarcodeBot.encode))
    application.add_handler(CommandHandler("decode", TelegramBarcodeBot.decode))
    
    # معالجة الصور المرسلة مباشرة
    application.add_handler(MessageHandler(filters.PHOTO, TelegramBarcodeBot.handle_photo))
    
    # رسالة لأي نص آخر
    async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❓ أمر غير معروف. استخدم /help لعرض الأوامر المتاحة.")
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    
    # تشغيل البوت
    print("🤖 البوت يعمل... اضغط Ctrl+C للإيقاف")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
