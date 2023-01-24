import os
import yfinance as yf
import plotly.graph_objects as go
import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


#API_KEY = os.getenv('API_KEY')
API_KEY = os.getenv('API_KEY')
bot = Bot(token=API_KEY)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start', 'help'])
async def help(message: types.Message):
    response =  f"<b>Commands:</b>\n" \
                f"/p &lt;stock name&gt; - stock price & yields\n" \
                f"/g &lt;stock name&gt; &lt;period&gt; - graph & rates\n" \
                f"/sp - my stock portfolio\n" \
                f"/time - get market status\n" \
                f"/help - get bot commands options"
    await message.answer(response, parse_mode='HTML')

@dp.message_handler(commands=['sp'])
async def get_stocks(message: types.Message):
    stock_data = []
    stocks = ['nvda', 'amzn', 'amd', 'qcom', 'googl', 'msft', 'gm', 'aapl', 'meta']
    minor_stocks = ['intc', 'ibm', 'nke', 'etsy', 'vrtx', 'mu', 'F', 'jpm', 'orcl', 'yum', 'pep']
    response = ""
    try:
        response += f"<b>Main Stocks</b>\n"
        for stock in stocks:
            data = yf.download(tickers=stock, period='7d', interval='1d')
            data = data.reset_index()

            response += f"\U0001F4B0  {stock} \n"
            stock_data.append([stock])
            columns = ['stock']
            for index, row in data.iterrows():
                stock_position = len(stock_data) - 1
                price = f"{row['Close']:.2f}"
                format_date = row['Date'].strftime('%d/%m/%y')
                response += "%s  %s\n" % (format_date, price)
                stock_data[stock_position].append(price)
                columns.append(format_date)

            stock_percent_change = calculate_stock_percantage_change(data)
            alert_emoji = "\U0001F534"
            green_emoji = "\U0001F7E2"
            stock_status_emoji = alert_emoji if stock_percent_change < 0 else green_emoji

            response += f"Weekly change: {stock_percent_change}% {stock_status_emoji}\n\n"
        response += f"------------------------------\n"
        response += f"<b>Minor Stocks</b>\n"
        for stock in minor_stocks:
            data = yf.download(tickers=stock, period='7d', interval='1d')
            data = data.reset_index()
            response += f"\U0001F4B0  {stock} \n"
            stock_data.append([stock])
            columns = ['stock']
            for index, row in data.iterrows():
                stock_position = len(stock_data) - 1
                price = f"{row['Close']:.2f}"
                format_date = row['Date'].strftime('%d/%m/%y')
                response += "%s  %s\n" % (format_date, price)
                stock_data[stock_position].append(price)
                columns.append(format_date)

            stock_percent_change = calculate_stock_percantage_change(data)
            alert_emoji = "\U0001F534"
            green_emoji = "\U0001F7E2"
            stock_status_emoji = alert_emoji if stock_percent_change < 0 else green_emoji

            response += f"Weekly change: {stock_percent_change}% {stock_status_emoji}\n\n"

    except Exception:
        response += f"Error occured. \n\n"
    await message.answer(response, parse_mode='html')

@dp.message_handler(commands=['time'])
async def time(message: types.Message):
    response = is_market_open()
    await message.answer(response, parse_mode='html')

def calculate_stock_percantage_change(data):
    if len(data) > 0:
        data['Close'].replace(to_replace=0, value=0.001, inplace=True)
        percent = (data['Close'][len(data) - 1] - data['Close'][0]) / (data['Close'][0]) * 100
        return float(f"{percent:.2f}")
    else:
        return False

def stock_price_by_period(message):
    status = False
    try:
        request = message.text.split()
    except Exception:
        request = message.data.split()

    if request[0].lower() == '/g':
        if len(request) ==3:
            if request[2] in ['1h', '1d', '7d', '1mo', '1y', 'max']:
                status = True
    return status

def get_interval(period):
    period_mapping_dict = {
        '1h': '2m',
        '1d' : '5m',
        '7d': '90m',
        '1mo': '1d',
        '1y': '5d',
        'max': '1wk',
    }
    return period_mapping_dict.get(period.lower(), False)

@dp.message_handler()
async def stock_price(message: types.Message):
    if stock_price_by_period(message):
        try:
            f_message = message.text.split()
        except Exception:
            f_message = message.data.split()
        period = f_message[2]
        interval = get_interval(period)

        if period and interval:
            stock_name = f_message[1].lower()
            data = yf.download(tickers=stock_name, period=period, interval=interval)
            if not data.empty :
                data.dropna(inplace=True)
                data = data.reset_index()
                if data.get('Datetime') is not None:
                    date = 'Datetime'
                elif data.get('Date') is not None:
                    date = 'Date'
                else:
                    date = 'index'

                response = f"<b>{stock_name}</b>\n"

                j = 0
                try:
                    for index, row in data.iterrows():
                        #if index % 5 == 1:  #show only first data in day
                        price = f"{row['Close']:.2f}"
                        format_date = row[date].strftime('%d/%m %H:%M') if period in ['1h', '1d'] else row[date].\
                            strftime('%d/%m/%y')
                        response += "%s  %s, " % (format_date, price)

                        j += 1
                        if j % 3 == 0:
                            response += "\n"

                    data["format_date"] = data[date].dt.strftime('%d/%m/ %H:%M') if period in ['1d','1h'] else \
                        data[date].dt.strftime('%d/%m/%y')
                    data.set_index('format_date', inplace=True)
                    per_change =  calculate_stock_percantage_change(data)
                    response = response [:-3]
                    response += f"\n\n{per_change}%\n"

                    if per_change < 0 :
                        line_color = '#B53737'
                        fig = go.Figure(data=go.Scatter(x=data.index, y=data['Close'], mode='lines', line_color=line_color))
                    elif per_change:
                        line_color = '#6B8E23'
                        fig = go.Figure(data=go.Scatter(x=data.index, y=data['Close'], mode='lines', line_color=line_color))
                    else:
                        line_color = '#ffe476'
                        fig = go.Figure(data=go.Scatter(x=data.index, y=data['Close'], mode='lines', line_color=line_color))

                    fig.update_layout(width=950, height=700, margin_t=50, margin_l=58, xaxis_rangeslider_visible=False,
                                      font={'family': 'Helvetica', 'color': '#000', 'size':15},
                                      title_font_size=16,
                                      title_font_family='Open Sans', paper_bgcolor='#fff',
                                      plot_bgcolor='#bdbdb2', title='<b>' + stock_name.upper() + ':</b>')
                    image_path= "images/fig1.png"
                    fig.write_image(image_path)

                    chat_id = message.chat.id if hasattr(message, 'chat') else message['message'].chat.id
                    await bot.send_photo(chat_id, open(image_path, "rb"), parse_mode='HTML')

                    button = InlineKeyboardButton(text='refresh', callback_game=message, callback_data=f"/g {stock_name} {period}")
                    keyboard_inline = InlineKeyboardMarkup().add(button)
                    await bot.send_message(chat_id, response, parse_mode='html', reply_markup=keyboard_inline)
                    return True
                except Exception:
                    return False
            else:
                error = "stock name is not valid. try again"
                await message.answer(error)
        else:
            error = "period is not valid. try hourly / daily / monthly / yearly / max"
            await message.answer(error)
    elif is_stock_change(message):
        try:
            stock_name = message.text.split()[1].lower()
        except Exception:
            stock_name = message.data.split()[1].lower()

        periods = ['60m', '1d', '7d', '1mo', '1y', 'max']
        intervals = ['5m', '90m', '90m', '90m', '5d','1wk']
        i = 0
        response = ""
        for period in periods:
            interval = intervals[i]
            i += 1

            data = yf.download(tickers=stock_name, period=period, interval=interval)
            if not data.empty:
                percentage_change = calculate_stock_percantage_change(data)
                emoji = get_emoji(percentage_change)
                response += f"{period}: {percentage_change}% {emoji}\n"
                if period == 'max':
                    current_price = f"{data['Close'][-1]:.2f}"

        out = "\U0001F4B0" + f" <b>{stock_name}</b>: {current_price}$\n"
        out += response
        button = InlineKeyboardButton(text='refresh', callback_game=message, callback_data=f"/p {stock_name}")
        markup = InlineKeyboardMarkup().add(button)

    else:
        out = "command is not valid try again."
        markup = None

    chat_id = message.chat.id if hasattr(message, 'chat') else message['message'].chat.id
    await bot.send_message(chat_id, out, parse_mode='html', reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith('/g '))
async def refresh_data(call: types.CallbackQuery):
    await stock_price(call)

@dp.callback_query_handler(lambda c: c.data.startswith('/p '))
async def refresh_weekly_data(call: types.CallbackQuery):
    await stock_price(call)

def is_stock_change(message):
    try:
        request = message.text.split()
    except Exception:
        request = message.data.split()

    if len(request) != 2 or request[0].lower() != '/p':
        return False
    else:
        return True

def get_emoji(percentage_change):
    neutral = "\U0001F610" # 0
    confused ="\U0001F615" # <= -0.5
    worried = "\U0001F61F" # <= -1.5
    sweat = "\U0001F632"   # <= 3
    crying = "\U0001F622"  # <= -7
    loudly_crying = "\U0001F62D" # < -7

    grinning = "\U0001F642"  # <=0.5
    smiling_small = "\U0001F600"  # <=1.5
    smiling_big = "\U0001F604"  # <=3
    beaming  = "\U0001F601"  # <=7
    money_face = "\U0001F911"  # >7

    if percentage_change == 0:
        return neutral
    elif percentage_change > 0:
        if percentage_change < 0.5:
            return grinning
        elif 0.5 <= percentage_change < 1.5:
            return smiling_small
        elif 1.5 <= percentage_change < 3:
            return smiling_big
        elif 3 <= percentage_change < 9:
            return beaming
        elif percentage_change >= 9:
            return money_face
    else:
        if percentage_change > -0.5:
            return confused
        if -0.5 >= percentage_change > -1.5:
            return worried
        elif -1.5 >= percentage_change > -3:
            return sweat
        elif -3 >= percentage_change > -9:
            return crying
        elif percentage_change <= -9:
            return loudly_crying

def get_market_status(status, hour, minutes_open):
    emoji = '\u2714\uFE0F' if status=='open' else '\u274C'
    if hour > 0 :
        if minutes_open > 0:
            if status == 'closed':
                return f"\U0001f1fa\U0001f1f8 {status}. {emoji} opens in {hour} Hours and {minutes_open} minutes."
            else:
                return f"\U0001f1fa\U0001f1f8 {status}. {emoji} closed in {23 - hour} Hours and {minutes_open} minutes."
        else:
            return f"\U0001f1fa\U0001f1f8 {status}. {emoji} opens in {hour} Hours ."
    else:
        return f"\U0001f1fa\U0001f1f8 {status}. {emoji} opens in {minutes_open} minutes."

def is_market_open():
    holiday_list = {
        '17/01/2022': '', '21/02/2022': '', '15/04/2022': '', '30/05/2022': '', '20/06/2022': '', '04/07/2022': '',
        '05/09/2022': '', '24/11/2022': '', '25/11/2022': 20, '26/12/2022': '', '02/01/2023': '', '16/01/2023': '',
        '20/02/2023': '', '07/04/2023': '', '29/05/2023': '', '19/06/2023': '', '04/07/2023': '', '04/09/2023': '',
        '23/11/2023': 20, '25/12/2023': '',
    }

    now = datetime.datetime.now()
    weekday = now.weekday()
    now_total_minutes = int(now.strftime('%H')) * 60 + int(now.strftime('%M'))

    if weekday != 5 and weekday != 6: # Monday is 0 and Sunday is 6.
        frmt_date = now.strftime('%d/%m/%Y')
        if frmt_date not in holiday_list.keys():
            if now_total_minutes > 0 and now_total_minutes < 990:
                minutes_open = (990 - now_total_minutes) % 60
                hour = int((990 - now_total_minutes) / 60)
                status = 'closed'
            elif now_total_minutes >= 990 and now_total_minutes < 1380:
                minutes_open = (1380 - now_total_minutes) % 60
                hour = int((1380 - minutes_open) / 60)
                status = 'open'
            else:
                hour = 17
                minutes_open = 30 - int(now.strftime('%M'))
                if minutes_open < 0:
                    hour = 16
                    minutes_open = 90 - int(now.strftime('%M'))
                status = 'closed'
        else:
            closing_hour = holiday_list[frmt_date] if holiday_list.get(frmt_date, False) else False
            if closing_hour:
                if now_total_minutes < 960:
                    status = 'closed'
                    minutes_delta = 960 - now_total_minutes
                    minutes_open = minutes_delta % 60
                    hour = int(minutes_open / 60)
                elif 960 < now_total_minutes < 1380:
                    status = 'open'
                    minutes_delta = 1380 - now_total_minutes
                    minutes_open = minutes_delta % 60
                    hour = int(minutes_open / 60)
                else:
                    status = 'closed'
                    minutes_delta = 1440 - now_total_minutes
                    minutes_open = minutes_delta % 60
                    hour = int(minutes_open / 60)
            else:
                status = 'closed'
                minutes_delta = 1440 - now_total_minutes
                minutes_open = minutes_delta % 60
                hour = int(minutes_open / 60)
    else:
        status = 'closed'
        if weekday == 5:
            minutes_delta = (990 + 48 * 60) - now_total_minutes
        else:
            minutes_delta = (990 + 24 * 60) - now_total_minutes
        minutes_open = minutes_delta % 60
        hour = int(minutes_delta / 60)

    return get_market_status(status=status, hour=hour, minutes_open=minutes_open)

executor.start_polling(dp)
