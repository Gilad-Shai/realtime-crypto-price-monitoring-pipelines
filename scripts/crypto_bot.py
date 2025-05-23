from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# Your bot token
TOKEN = "7544061098:AAEufQYoo1cl1rQlsUltqO9CB3neeKy3YzU"

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Crypto Alert Bot!\nUse /price <coin> to get the current price.\nExample: /price bitcoin"
    )

# Command: /price <coin>
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("❗ Please provide a coin name. Example: /price ethereum")
        return

    coin = context.args[0].lower()
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"

    response = requests.get(url)
    data = response.json()

    if coin in data:
        price = data[coin]["usd"]
        await update.message.reply_text(f"💰 {coin.capitalize()} price: ${price}")
    else:
        await update.message.reply_text(f"⚠️ Could not find price for '{coin}'. Please check the name.")

# Main application
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))

    print("🤖 Bot is running...")
    app.run_polling()
