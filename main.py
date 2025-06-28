#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
from telebot import types
from telebot.util import quick_markup
import json
import os
import time
import signal
import sys
from datetime import datetime
import logging
import threading
from config import BOT_TOKEN, DATA_FILE

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# متغير للتحكم في حالة التشغيل
running = True

# معالج الإشارات لإيقاف البوت بشكل آمن
def signal_handler(sig, frame):
    global running
    logger.info("تم استلام إشارة إيقاف. جاري إيقاف البوت بشكل آمن...")
    running = False
    sys.exit(0)

# تسجيل معالج الإشارات
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# إنشاء كائن البوت
bot = telebot.TeleBot(BOT_TOKEN)

# قاموس شامل للوحدات
conversion_factors = {
    'العزم': {
        'N·m': 1, 'kN·m': 0.001, 'kgf·m': 0.101971621,
        'lbf·ft': 0.737562149, 'lbf·in': 8.85074579,
        'ozf·in': 141.611933, 'dyn·cm': 10000000
    },
    'المساحة': {
        'm²': 1, 'cm²': 10000, 'mm²': 1000000,
        'ft²': 10.7639104, 'in²': 1550.0031,
        'hectare': 0.0001, 'acre': 0.000247105,
        'yard²': 1.19599005, 'mile²': 3.86102e-7
    },
    'الحجم': {
        'm³': 1, 'l': 1000, 'cm³': 1000000,
        'mm³': 1000000000, 'ft³': 35.3146667,
        'in³': 61023.7441, 'gal (US)': 264.172052,
        'gal (UK)': 219.969248, 'barrel': 6.28981,
        'pint (US)': 2113.37642, 'pint (UK)': 1759.75399
    },
    'الضغط/الإجهاد': {
        'Pa': 1, 'kPa': 0.001, 'MPa': 0.000001,
        'GPa': 0.000000001, 'kgf/cm²': 0.0000101972,
        'kgf/m²': 0.101971621, 'psi': 0.000145038,
        'ksi': 0.000000145038, 'bar': 0.00001,
        'atm': 0.00000986923, 'Torr': 0.00750062,
        'mmHg': 0.00750062, 'mH2O': 0.000101972
    },
    'الطول': {
        'm': 1, 'km': 0.001, 'cm': 100,
        'mm': 1000, 'μm': 1000000, 'nm': 1000000000,
        'ft': 3.2808399, 'in': 39.3700787,
        'yd': 1.0936133, 'mile': 0.000621371,
        'nautical mile': 0.000539957, 'light-year': 1.057e-16
    },
    'الكتلة': {
        'kg': 1, 'g': 1000, 'mg': 1000000,
        'ton': 0.001, 'lb': 2.20462262,
        'oz': 35.2739619, 'carat': 5000,
        'tonne': 0.001, 'slug': 0.0685218,
        'stone': 0.157473
    },
    'القوة': {
        'N': 1, 'kN': 0.001, 'kgf': 0.101971621,
        'lbf': 0.224808943, 'dyne': 100000,
        'kip': 0.000224809, 'poundal': 7.23301
    },
    'الزمن': {
        's': 1, 'ms': 1000, 'μs': 1000000,
        'min': 1/60, 'h': 1/3600, 'day': 1/86400,
        'week': 1/604800, 'month': 1/2.628e6,
        'year': 1/3.154e7
    },
    'درجة الحرارة': {
        '°C': 'celsius', '°F': 'fahrenheit', 
        'K': 'kelvin', '°R': 'rankine'
    },
    'السرعة': {
        'm/s': 1, 'km/h': 3.6, 'mph': 2.23694,
        'knot': 1.94384, 'ft/s': 3.28084,
        'c': 3.3356e-9
    },
    'الطاقة': {
        'J': 1, 'kJ': 0.001, 'cal': 0.239006,
        'kcal': 0.000239006, 'Wh': 0.000277778,
        'kWh': 2.7778e-7, 'eV': 6.242e18,
        'BTU': 0.000947817, 'ft·lbf': 0.737562
    }
}

def load_user_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"خطأ في قراءة ملف البيانات: {e}")
            return {}
    return {}

def save_user_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"خطأ في حفظ ملف البيانات: {e}")

def convert_temperature(value, from_unit, to_unit):
    try:
        value = float(value)
        if from_unit == '°C':
            if to_unit == '°F':
                return value * 9/5 + 32
            elif to_unit == 'K':
                return value + 273.15
            elif to_unit == '°R':
                return (value + 273.15) * 9/5
        elif from_unit == '°F':
            if to_unit == '°C':
                return (value - 32) * 5/9
            elif to_unit == 'K':
                return (value - 32) * 5/9 + 273.15
            elif to_unit == '°R':
                return value + 459.67
        elif from_unit == 'K':
            if to_unit == '°C':
                return value - 273.15
            elif to_unit == '°F':
                return (value - 273.15) * 9/5 + 32
            elif to_unit == '°R':
                return value * 9/5
        elif from_unit == '°R':
            if to_unit == '°C':
                return (value - 491.67) * 5/9
            elif to_unit == '°F':
                return value - 459.67
            elif to_unit == 'K':
                return value * 5/9
        return value
    except Exception as e:
        logger.error(f"خطأ في تحويل درجة الحرارة: {e}")
        return value

# تحميل بيانات المستخدمين
user_data = load_user_data()

# وظيفة للتحقق من حالة البوت وإرسال إشعار
def send_status_notification():
    try:
        me = bot.get_me()
        logger.info(f"البوت يعمل بشكل طبيعي: {me.first_name} (@{me.username})")
        return True
    except Exception as e:
        logger.error(f"فشل في الاتصال بالبوت: {e}")
        return False

# وظيفة مراقبة البوت
def monitor_bot():
    while running:
        try:
            if not send_status_notification():
                logger.warning("البوت غير متصل، محاولة إعادة الاتصال...")
            time.sleep(300)  # التحقق كل 5 دقائق
        except Exception as e:
            logger.error(f"خطأ في وظيفة المراقبة: {e}")
            time.sleep(60)  # انتظار دقيقة قبل المحاولة مرة أخرى

@bot.message_handler(commands=['start', 'help', 'restart'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    if chat_id not in user_data:
        user_data[chat_id] = {
            'conversion_history': [],
            'preferred_units': {},
            'step': None,
            'value': None,
            'category': None,
            'from_unit': None
        }
        save_user_data(user_data)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_convert = types.KeyboardButton('تحويل الوحدات 📊')
    btn_history = types.KeyboardButton('سجل التحويلات 🕒')
    btn_settings = types.KeyboardButton('الإعدادات ⚙️')
    btn_help = types.KeyboardButton('مساعدة ℹ️')
    markup.add(btn_convert, btn_history, btn_settings, btn_help)
    
    welcome_msg = """
<b>مرحباً بك في بوت تحويل الوحدات المتقدم!</b> 🚀

اضغط على "تحويل الوحدات 📊" لبدء عملية تحويل جديدة، أو "مساعدة ℹ️" لعرض دليل الاستخدام.
    """
    bot.send_message(chat_id, welcome_msg, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == 'مساعدة ℹ️')
def show_help(message):
    help_text = """
<b>🎓 دليل استخدام البوت:</b>

1. <b>تحويل الوحدات 📊</b>:
- ابدأ عملية تحويل جديدة
- اختر الفئة والوحدات المناسبة
- احصل على النتيجة مع تفاصيل التحويل

2. <b>سجل التحويلات 🕒</b>:
- عرض آخر 10 عمليات تحويل
- إمكانية إعادة استخدام التحويلات السابقة

3. <b>الإعدادات ⚙️</b>:
- تعيين الوحدات المفضلة لكل فئة
- إعادة تعيين الإعدادات
"""
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == 'تحويل الوحدات 📊')
def start_conversion(message):
    chat_id = str(message.chat.id)
    user_data[chat_id]['step'] = 'waiting_for_value'
    user_data[chat_id]['value'] = None
    user_data[chat_id]['category'] = None
    user_data[chat_id]['from_unit'] = None
    save_user_data(user_data)
    
    bot.send_message(chat_id, "📝 الرجاء إدخال القيمة الرقمية التي تريد تحويلها:")

@bot.message_handler(func=lambda message: user_data.get(str(message.chat.id), {}).get('step') == 'waiting_for_value')
def get_value(message):
    chat_id = str(message.chat.id)
    try:
        value = float(message.text)
        user_data[chat_id]['value'] = value
        user_data[chat_id]['step'] = 'waiting_for_category'
        save_user_data(user_data)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        buttons = [types.KeyboardButton(category) for category in conversion_factors.keys()]
        btn_cancel = types.KeyboardButton('إلغاء ❌')
        markup.add(*buttons, btn_cancel)
        
        bot.send_message(chat_id, f"✅ تم حفظ القيمة: <b>{value}</b>\n\nالرجاء اختيار نوع الوحدات:", reply_markup=markup, parse_mode='HTML')
    except ValueError:
        bot.send_message(chat_id, "⚠️ الرجاء إدخال رقم صحيح أو عشري صحيح. حاول مرة أخرى:")

@bot.message_handler(func=lambda message: user_data.get(str(message.chat.id), {}).get('step') == 'waiting_for_category')
def get_category(message):
    chat_id = str(message.chat.id)
    if message.text not in conversion_factors:
        bot.send_message(chat_id, "⚠️ الرجاء اختيار نوع وحدات صحيح من الأزرار المعروضة.")
        return
    
    user_data[chat_id]['category'] = message.text
    user_data[chat_id]['step'] = 'waiting_for_from_unit'
    save_user_data(user_data)
    
    preferred_units = user_data[chat_id].get('preferred_units', {}).get(message.text, [])
    all_units = list(conversion_factors[message.text].keys())
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    
    if preferred_units:
        for unit in preferred_units:
            if unit in all_units:
                markup.add(types.KeyboardButton(unit))
    
    other_units = [unit for unit in all_units if unit not in preferred_units]
    buttons = [types.KeyboardButton(unit) for unit in other_units]
    
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i+3])
    
    btn_cancel = types.KeyboardButton('إلغاء ❌')
    markup.add(btn_cancel)
    
    bot.send_message(chat_id, f"🔽 اختر الوحدة الأصلية (الوحدة الحالية للقيمة):", reply_markup=markup)

@bot.message_handler(func=lambda message: user_data.get(str(message.chat.id), {}).get('step') == 'waiting_for_from_unit')
def get_from_unit(message):
    chat_id = str(message.chat.id)
    user_state = user_data[chat_id]
    category = user_state['category']
    
    if message.text == 'إلغاء ❌':
        cancel_operation(message)
        return
    
    if message.text not in conversion_factors[category]:
        bot.send_message(chat_id, "⚠️ الرجاء اختيار وحدة صحيحة من الأزرار المعروضة.")
        return
    
    user_state['from_unit'] = message.text
    user_state['step'] = 'waiting_for_to_unit'
    save_user_data(user_data)
    
    preferred_units = user_state.get('preferred_units', {}).get(category, [])
    all_units = list(conversion_factors[category].keys())
    all_units.remove(message.text)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    
    if preferred_units:
        for unit in preferred_units:
            if unit in all_units and unit != message.text:
                markup.add(types.KeyboardButton(unit))
    
    other_units = [unit for unit in all_units if unit not in preferred_units]
    buttons = [types.KeyboardButton(unit) for unit in other_units]
    
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i+3])
    
    btn_cancel = types.KeyboardButton('إلغاء ❌')
    markup.add(btn_cancel)
    
    bot.send_message(chat_id, f"🔼 اختر الوحدة الهدف (الوحدة الجديدة للتحويل):", reply_markup=markup)

@bot.message_handler(func=lambda message: user_data.get(str(message.chat.id), {}).get('step') == 'waiting_for_to_unit')
def perform_conversion(message):
    chat_id = str(message.chat.id)
    user_state = user_data[chat_id]
    
    if message.text == 'إلغاء ❌':
        cancel_operation(message)
        return
    
    category = user_state['category']
    if message.text not in conversion_factors[category]:
        bot.send_message(chat_id, "⚠️ الرجاء اختيار وحدة صحيحة من الأزرار المعروضة.")
        return
    
    value = user_state['value']
    from_unit = user_state['from_unit']
    to_unit = message.text
    
    if category == 'درجة الحرارة':
        converted_value = convert_temperature(value, from_unit, to_unit)
        from_to_factor = None
        to_from_factor = None
    else:
        try:
            factor_from = conversion_factors[category][from_unit]
            factor_to = conversion_factors[category][to_unit]
            converted_value = (value / factor_from) * factor_to
            from_to_factor = (1 / factor_from) * factor_to
            to_from_factor = factor_from / factor_to
        except Exception as e:
            logger.error(f"خطأ في التحويل: {e}")
            bot.send_message(chat_id, "⚠️ حدث خطأ أثناء التحويل. الرجاء المحاولة مرة أخرى.")
            return
    
    conversion_record = {
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'value': value,
        'from_unit': from_unit,
        'to_unit': to_unit,
        'result': converted_value,
        'category': category
    }
    
    if 'conversion_history' not in user_state:
        user_state['conversion_history'] = []
    user_state['conversion_history'].append(conversion_record)
    
    if len(user_state['conversion_history']) > 10:
        user_state['conversion_history'] = user_state['conversion_history'][-10:]
    
    if isinstance(converted_value, float):
        if abs(converted_value) < 0.0001 or abs(converted_value) > 1000000:
            result_str = "{:.4e}".format(converted_value)
        else:
            result_str = "{:.4f}".format(converted_value)
    else:
        result_str = str(converted_value)
    
    result_message = f"""
<b>🎯 نتيجة التحويل:</b>
<b>{value}</b> {from_unit} = <b>{result_str}</b> {to_unit}
"""
    
    if category != 'درجة الحرارة':
        result_message += f"""
<b>📊 تفاصيل التحويل:</b>
1 {from_unit} = {from_to_factor:.6f} {to_unit}
1 {to_unit} = {to_from_factor:.6f} {from_unit}
"""
    
    markup = quick_markup({
        'تحويل مرة أخرى': {'callback_data': f'convert_again_{category}_{from_unit}_{value}'},
        'حفظ في المفضلة': {'callback_data': f'save_favorite_{category}_{from_unit}_{to_unit}'},
        'إلغاء': {'callback_data': 'cancel'}
    }, row_width=2)
    
    bot.send_message(chat_id, result_message, reply_markup=markup, parse_mode='HTML')
    
    user_state['step'] = None
    save_user_data(user_data)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = str(call.message.chat.id)
    data = call.data
    
    if data.startswith('convert_again_'):
        try:
            _, category, from_unit, value = data.split('_', 3)
            value = float(value)
            
            user_data[chat_id]['step'] = 'waiting_for_to_unit'
            user_data[chat_id]['value'] = value
            user_data[chat_id]['category'] = category
            user_data[chat_id]['from_unit'] = from_unit
            save_user_data(user_data)
            
            preferred_units = user_data[chat_id].get('preferred_units', {}).get(category, [])
            all_units = list(conversion_factors[category].keys())
            all_units.remove(from_unit)
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            
            if preferred_units:
                for unit in preferred_units:
                    if unit in all_units and unit != from_unit:
                        markup.add(types.KeyboardButton(unit))
            
            other_units = [unit for unit in all_units if unit not in preferred_units]
            buttons = [types.KeyboardButton(unit) for unit in other_units]
            
            for i in range(0, len(buttons), 3):
                markup.add(*buttons[i:i+3])
            
            btn_cancel = types.KeyboardButton('إلغاء ❌')
            markup.add(btn_cancel)
            
            bot.send_message(chat_id, f"🔄 اختر الوحدة الجديدة للتحويل من {value} {from_unit}:", reply_markup=markup)
        except Exception as e:
            logger.error(f"خطأ في معالجة callback: {e}")
            bot.send_message(chat_id, "⚠️ حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى.")
    
    elif data.startswith('save_favorite_'):
        try:
            _, category, from_unit, to_unit = data.split('_', 3)
            
            if 'preferred_units' not in user_data[chat_id]:
                user_data[chat_id]['preferred_units'] = {}
            if category not in user_data[chat_id]['preferred_units']:
                user_data[chat_id]['preferred_units'][category] = []
            
            if from_unit not in user_data[chat_id]['preferred_units'][category]:
                user_data[chat_id]['preferred_units'][category].append(from_unit)
            if to_unit not in user_data[chat_id]['preferred_units'][category]:
                user_data[chat_id]['preferred_units'][category].append(to_unit)
            
            save_user_data(user_data)
            bot.answer_callback_query(call.id, "تم حفظ الوحدات في المفضلة بنجاح!")
        except Exception as e:
            logger.error(f"خطأ في حفظ المفضلة: {e}")
            bot.answer_callback_query(call.id, "⚠️ حدث خطأ أثناء الحفظ. الرجاء المحاولة لاحقاً.")
    
    elif data == 'cancel':
        bot.delete_message(chat_id, call.message.message_id)
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text == 'سجل التحويلات 🕒')
def show_history(message):
    chat_id = str(message.chat.id)
    history = user_data.get(chat_id, {}).get('conversion_history', [])
    
    if not history:
        bot.send_message(chat_id, "⚠️ لا يوجد سجل تحويلات حتى الآن.")
        return
    
    history_text = "<b>🕒 سجل آخر 10 تحويلات:</b>\n\n"
    for i, record in enumerate(reversed(history), 1):
        value = record['value']
        from_unit = record['from_unit']
        to_unit = record['to_unit']
        result = record['result']
        category = record['category']
        date = record['date']
        
        if isinstance(result, float):
            if abs(result) < 0.0001 or abs(result) > 1000000:
                result_str = "{:.4e}".format(result)
            else:
                result_str = "{:.4f}".format(result)
        else:
            result_str = str(result)
        
        history_text += f"<b>{i}. {category}:</b> {value} {from_unit} ➡️ {result_str} {to_unit}\n<i>{date}</i>\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, record in enumerate(reversed(history)):
        btn_text = f"{record['category']}: {record['value']} {record['from_unit']} ➡️ {record['to_unit']}"
        callback_data = f"history_{i}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    bot.send_message(chat_id, history_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == 'الإعدادات ⚙️')
def show_settings(message):
    chat_id = str(message.chat.id)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_preferred = types.InlineKeyboardButton("إدارة الوحدات المفضلة 🌟", callback_data="manage_preferred")
    btn_reset = types.InlineKeyboardButton("إعادة تعيين الإعدادات 🔄", callback_data="reset_settings")
    markup.add(btn_preferred, btn_reset)
    
    bot.send_message(chat_id, "<b>⚙️ إعدادات البوت:</b>\n\nاختر الإعداد الذي تريد تغييره:", reply_markup=markup, parse_mode='HTML')

def cancel_operation(message):
    chat_id = str(message.chat.id)
    user_data[chat_id]['step'] = None
    save_user_data(user_data)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_convert = types.KeyboardButton('تحويل الوحدات 📊')
    btn_history = types.KeyboardButton('سجل التحويلات 🕒')
    btn_settings = types.KeyboardButton('الإعدادات ⚙️')
    btn_help = types.KeyboardButton('مساعدة ℹ️')
    markup.add(btn_convert, btn_history, btn_settings, btn_help)
    
    bot.send_message(chat_id, "❌ تم إلغاء العملية الحالية.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def default_handler(message):
    chat_id = str(message.chat.id)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_convert = types.KeyboardButton('تحويل الوحدات 📊')
    btn_history = types.KeyboardButton('سجل التحويلات 🕒')
    btn_settings = types.KeyboardButton('الإعدادات ⚙️')
    btn_help = types.KeyboardButton('مساعدة ℹ️')
    markup.add(btn_convert, btn_history, btn_settings, btn_help)
    
    bot.send_message(chat_id, "⚠️ أمر غير معروف. الرجاء استخدام الأزرار أدناه:", reply_markup=markup)

# وظيفة للتعامل مع الأخطاء
def handle_exception(exception):
    logger.error(f"حدث خطأ غير متوقع: {exception}")
    try:
        # محاولة إعادة الاتصال
        bot.stop_polling()
        time.sleep(10)
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        logger.error(f"فشل في إعادة الاتصال: {e}")

# تشغيل البوت مع التعامل مع الأخطاء
if __name__ == "__main__":
    logger.info("بدء تشغيل البوت...")
    
    # بدء خيط المراقبة
    monitor_thread = threading.Thread(target=monitor_bot)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # إرسال إشعار بدء التشغيل
    send_status_notification()
    
    # تشغيل البوت مع آلية إعادة المحاولة
    while running:
        try:
            logger.info("بدء وضع الاستطلاع...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, restart_on_change=True)
        except Exception as e:
            handle_exception(e)
            logger.error(f"انقطع الاتصال: {e}. إعادة المحاولة بعد 10 ثوانٍ...")
            time.sleep(10)
