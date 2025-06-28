import os
import json
import logging
from pathlib import Path

# إعداد المسارات
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = os.path.join(BASE_DIR, "unit_conversion_data.json")

# تحميل التوكن من متغيرات البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# إذا لم يتم العثور على التوكن في متغيرات البيئة، استخدم القيمة الافتراضية
if not BOT_TOKEN:
    BOT_TOKEN = '7829695023:AAGlRS6LGsumiY-cZUiYGPk0hjzblf_fCiQ'

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "bot.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تأكد من وجود ملف البيانات
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)
    logger.info(f"تم إنشاء ملف البيانات: {DATA_FILE}")
