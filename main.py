
import phonenumbers, os, zipfile, tempfile
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.utils import executor
from collections import defaultdict
import pandas as pd
from search_engine import search_in_dbs

API_TOKEN = '7206134560:AAFn_f7ZqgV62DAoio2PPqZQMDwj7nGdVCY'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

os.makedirs("dbs", exist_ok=True)

user_history = defaultdict(list)
def get_phone_info(phone):
    try:
        parsed_number = phonenumbers.parse(phone)
        
        if not phonenumbers.is_valid_number(parsed_number):
            return None
        
        country = phonenumbers.region_code_for_number(parsed_number)
        number_type = phonenumbers.number_type(parsed_number)
        
        number_type_str = ""
        if number_type == phonenumbers.PhoneNumberType.MOBILE:
            number_type_str = "Мобильный"
        elif number_type == phonenumbers.PhoneNumberType.FIXED_LINE:
            number_type_str = "Стационарный"
        elif number_type == phonenumbers.PhoneNumberType.SHARED_COST:
            number_type_str = "Общий тариф"
        elif number_type == phonenumbers.PhoneNumberType.UNKNOWN:
            number_type_str = "Неизвестный"

        return {
            "valid": True,
            "country": country,
            "number_type": number_type_str,
            "formatted_number": phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        }
    except phonenumbers.phonenumberutil.NumberParseException:
        return None

@dp.message_handler(commands=['hlr'])
async def hlr_command(message: types.Message):
    phone_numbers = message.get_args().strip().split(',')
    
    if not phone_numbers:
        await message.reply("Пожалуйста, укажите номера телефонов через запятую.")
        return

    response = "Информация о номерах:\n"
    
    for phone in phone_numbers:
        phone = phone.strip()
        phone_info = get_phone_info(phone)
        
        if not phone_info:
            response += f"📱 Номер: {phone} - Неверный номер или невалидный формат.\n"
        else:
            response += (
                f"📱 Номер: {phone_info['formatted_number']}\n"
                f"🌍 Страна: {phone_info['country']}\n"
                f"📞 Тип: {phone_info['number_type']}")

    await message.reply(response, parse_mode="Markdown")

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.reply("Привет! Пришли мне файл с таблицей (CSV, Excel, DOCX, SQL и т.п.) — я его обработаю.")

@dp.message_handler(commands=['list'])
async def list_cmd(message: types.Message):
    files = os.listdir("dbs/")
    if not files:
        await message.reply("Нет загруженных баз данных.")
        return
    msg = "Загруженные базы:\n" + "\n".join(f"- {f}" for f in files)
    await message.reply(msg)

@dp.message_handler(lambda message: not message.text.startswith('/'))
async def handle_search(message: types.Message):
    query = message.text.strip()
    user_history[message.from_user.id].append(query)
    results = search_in_dbs(query)
    if not results:
        await message.reply("Ничего не найдено.")
        return

    full_text = "\n\n".join(results)
    if len(full_text) < 4000:
        await message.reply(full_text, parse_mode='HTML')
    else:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt", encoding='utf-8') as temp_file:
            temp_file.write(full_text)
            temp_file_path = temp_file.name

        doc = InputFile(temp_file_path, filename="search_results.txt")
        await message.reply_document(doc)

@dp.message_handler(commands=['search'])
async def column_search(message: types.Message):
    parts = message.text.strip().split(maxsplit=2)
    if len(parts) != 3:
        await message.reply("Используй: /search <столбец> <значение>")
        return
    column, value = parts[1], parts[2]
    from search_engine import search_in_column
    results = search_in_column(column, value)
    if not results:
        await message.reply("Ничего не найдено.")
        return
    for res in results:
        await message.reply(res)


@dp.message_handler(commands=['history'])
async def show_history(message: types.Message):
    history = user_history.get(message.from_user.id, [])
    if not history:
        await message.reply("История пуста.")
    else:
        await message.reply("Твои последние запросы:\n" + "\n".join(f"- {q}" for q in history[-10:]))

@dp.message_handler(commands=['delete'])
async def delete_db(message: types.Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) != 2:
        await message.reply("Укажи имя файла: /delete filename.csv")
        return
    filename = parts[1]
    path = os.path.join("dbs", filename)
    if os.path.exists(path):
        os.remove(path)
        await message.reply(f"Файл {filename} удалён.")
    else:
        await message.reply("Файл не найден.")

async def save_and_parse_file(file: types.Document, user_id: str):
    ext = file.file_name.split('.')[-1]
    valid_exts = ['csv', 'xls', 'xlsx', 'docx', 'sql', 'zip']
    if ext.lower() not in valid_exts:
        return None
    path = f"dbs/{user_id}_{file.file_name}"
    await file.download(destination_file=path)

    if ext == 'zip':
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall("dbs/")
        os.remove(path)
        return "zip"
    return path

@dp.message_handler(commands=['stats'])
async def stats_cmd(message: types.Message):
    msg = []
    for file in os.listdir("dbs/"):
        path = os.path.join("dbs", file)
        try:
            df = pd.read_csv(path, sep=None, engine='python')
            msg.append(f"📊 {file} — {len(df)} записей, {len(df.columns)} столбцов.")
        except Exception:
            continue
    if not msg:
        await message.reply("Нет данных для анализа.")
    else:
        await message.reply("\n".join(msg))

if __name__ == '__main__':
    print("Бот запущен!")
    executor.start_polling(dp)