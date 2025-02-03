import qrcode
import io
import os
import numpy as np
from telegram import Update, InputFile, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

application = Application.builder().token(TOKEN).build()

MENU_BUTTONS = {
    "Generate QR": "/QR <text>",
    "Styled QR": "/StyledQR <text>",
    "File QR": "Reply with /FileQR",
    "Help": "/help"
}
menu_markup = ReplyKeyboardMarkup(
    [
        ["Generate QR", "Styled QR"],
        ["File QR", "Help"]
    ],
    resize_keyboard=True
)


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "👋 **Welcome to The QR Code Bot!** 🎉\n\n"
        "✨ This bot helps you generate QR codes easily!\n\n"
        "📌 Use the following commands:\n\n"
        "🔹 `/QR <text>` - Generate a **simple QR Code** 📷\n"
        "🔹 `/StyledQR <text>` - Generate a **gradient-styled QR Code** 🎨\n"
        "🔹 `/FileQR` - **Reply to a file** to generate its QR Code 📂\n"
        "🔹 `/help` - Get more information ℹ️\n\n"
        "**Tap a button below to get started!** ⬇️\n\n"
        "📩 **Need more assistance? Feel free to reach out!**\n"
        "👤 **Author:** [Anurag Mahapatra](tg://user?id=1416085855)\n"
        "🌐 **GitHub:** [IAnuragMahapatra](https://github.com/IAnuragMahapatra)",
        reply_markup=menu_markup,
        parse_mode="Markdown"
    )


def create_qr(data: str, fill_color="black", back_color="white") -> io.BytesIO:
    qr = qrcode.QRCode(
        version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color,
                        back_color=back_color).convert("RGB")
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio


def create_gradient_qr(data: str, gradient_colors=((230, 230, 250), (148, 0, 211))) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="white", back_color="black").convert("RGBA")
    width, height = qr_image.size
    qr_array = np.array(qr_image)

    gradient = np.linspace(
        gradient_colors[0], gradient_colors[1], height).astype(np.uint8)
    gradient = np.repeat(gradient[:, np.newaxis, :], width, axis=1)

    mask = (qr_array[:, :, :3] == [255, 255, 255]).all(axis=2)
    qr_array[mask] = np.concatenate(
        [gradient[mask], np.full((mask.sum(), 1), 255)], axis=1)

    bio = io.BytesIO()
    Image.fromarray(qr_array, "RGBA").save(bio, format='PNG')
    bio.seek(0)
    return bio


async def generate_qr(update: Update, context: CallbackContext):
    message = ' '.join(context.args) if context.args else None
    if not message:
        await update.message.reply_text(
            "⚠️ *Error:* No text provided!\n\n"
            "✅ Usage: `/QR <text>`\n"
            "Example: `/QR Hello, World!`",
            parse_mode="Markdown"
        )
        return
    await update.message.reply_photo(photo=InputFile(create_qr(message), filename="qr_code.png"))


async def generate_styled_qr(update: Update, context: CallbackContext):
    message = ' '.join(context.args) if context.args else None
    if not message:
        await update.message.reply_text(
            "⚠️ *Error:* No text provided!\n\n"
            "✅ Usage: `/StyledQR <text>`\n"
            "Example: `/StyledQR Hello, World!`",
            parse_mode="Markdown"
        )
        return
    await update.message.reply_photo(photo=InputFile(create_gradient_qr(message), filename="lavender_qr_code.png"))


async def generate_file_qr(update: Update, context: CallbackContext):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("⚠️ *Error:* Reply to a file to generate its QR Code.", parse_mode="Markdown")
        return
    file = await update.message.reply_to_message.document.get_file()
    await update.message.reply_photo(photo=InputFile(create_qr(file.file_path), filename="file_qr.png"))


async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📖 **QR Code Bot Help Guide** ℹ️\n\n"
        "🤖 **How to use this bot?**\n"
        "Just use the commands below or tap a menu button!\n\n"
        "📌 **Commands:**\n"
        "🔹 `/QR <text>` - Generate a **standard QR Code** 📷\n"
        "🔹 `/StyledQR <text>` - Create a **gradient-styled QR Code** 🎨\n"
        "🔹 `/FileQR` - **Reply to a file** to generate its QR Code 📂\n"
        "🔹 `/help` - Show this help message ℹ️\n\n",
        parse_mode="Markdown"
    )


async def handle_button_press(update: Update, context: CallbackContext):
    await update.message.reply_text(MENU_BUTTONS.get(update.message.text, "Invalid option."))


application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('QR', generate_qr))
application.add_handler(CommandHandler('StyledQR', generate_styled_qr))
application.add_handler(CommandHandler('FileQR', generate_file_qr))
application.add_handler(CommandHandler('help', help_command))
application.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND, handle_button_press))

if __name__ == "__main__":
    application.run_polling()
