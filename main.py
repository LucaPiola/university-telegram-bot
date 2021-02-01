from getpass import getpass
import time
import os
import shutil
import logging
import liucAPI as LIUC
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

LOGIN, INSERT_USER, INSERT_PASSWORD, ACTIVITIES,  BIO = range(5)

username_esse3 = ""
password_esse3 = ""
thumbs_up_emoji = u'\U0001F44D' 

def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Login']]
    
    update.message.reply_text(
        u'\U0001F393' 
        ' Benvenuto in Tele-LIUC '
        u'\U0001F393' 
        '\n\nQuesto BOT non è ufficiale! \n'
        'Clicca su LOGIN per entrare '
        
        ,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
   
           
 

    return LOGIN

#ask for username
def login(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Choose of %s: %s", user.first_name, update.message.text)
    update.message.reply_text(
        'Inserisci l\'username:  (es. pi69.pinguino)',
        reply_markup=ReplyKeyboardRemove(),
    )

    return INSERT_USER

#save username and ask password 
def insert_user(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Username of %s: %s", user.first_name, update.message.text)
    username_esse3 = update.message.text
    context.user_data['user'] = username_esse3 #add entered username to global context
    update.message.reply_text(
        'Inserisci la password: (non verrà salvata)'
    )

    return INSERT_PASSWORD

#save password and ask next operation (get grades, available exams, average...)
def insert_password(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    #print(context.user_data['user'])
    logger.info("Password of %s: %s", user.first_name, update.message.text)
    password_esse3 = update.message.text
    context.user_data['pass'] = password_esse3 #add entered pass to global context
    """ update.message.reply_text(
        "Entro in sol.liuc.it... "
    ) """
    user = context.user_data['user']
    password = context.user_data['pass']
    update.message.delete() #cancella password inserita per sicurezza
    #connect to esse 3 API
    try:
        logged_info = LIUC.login(user, password)
        name = logged_info[3]
        surname = logged_info[4]
    except:
        print("Credenziali errate: ")
        reply_keyboard = [["/start"]]
        update.message.reply_text("Credenziali errate, clicca su /start per riprovare.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),)
        return ConversationHandler.END
 
    welcome_message = "Ciao " + name + " " + ", scegli un'opzione: "
    #print on telegram possible choices 
    reply_keyboard = [['Esiti', 'Libretto', 'Appelli', 'Media', 'Tasse', 'Chiudi']]
    update.message.reply_text(
    welcome_message,
    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
)

    
    return ACTIVITIES


def activities(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    username1 = context.user_data['user']
    password = context.user_data['pass']
    
    url = "https://sol.liuc.it/e3rest/api/"
    

    choice = update.message.text
    

    if choice == 'Libretto':
        lista_libretto = LIUC.get_libretto(username1, password)[0]
        numero_esami_dati = LIUC.get_libretto(username1, password)[1]
        msg_libretto = ""
        for i in range(len(lista_libretto)-1):
            msg_libretto = msg_libretto + "\n\n*" + str(lista_libretto[i][0]) + "* - " + str(lista_libretto[i][1])
        
        msg_libretto = msg_libretto + "\n\n" + "Esami dati: " + str(numero_esami_dati[0]) + "\nEsami da dare: " + str(numero_esami_dati[1])
        update.message.reply_text(msg_libretto, parse_mode='Markdown')


    LIUC.liucLogin(username1, password)

    #print last marks
    if choice == 'Esiti':
        LIUC.liucLogin(username1, password)

        try:
            
            esito = LIUC.get_last_mark(username1, password)
            for i in range(len(esito)):
                invia_esito = u'\U0001F393' + " " + esito[i]
                update.message.reply_text(invia_esito)
        except:
            #da fixare: se si cerca due volte gli esiti non ne trova
            update.message.reply_text("Impossibile trovare esiti, riprova. ")
        

    #print next available exams
    if choice == 'Appelli':

        lista_appelli = ""
        #get list with all the exams
        print_appelli = (LIUC.getAppelli(username1, password))
        
        for i in range(len(print_appelli)):
           
            try:
                if int((print_appelli[i][1])[6:10]) >= 2021: #if it's an old exam, it won't be sent 
                    lista_appelli = lista_appelli + "\n\n *" + print_appelli[i][0] + "* \n" + print_appelli[i][2] + "\n" + (print_appelli[i][1])[0:10]  
                    #if open and closing dates for exam application are needed, add in lista_appelli 
                    #this string:
                    #   + (print_appelli[i][3])[0:10]  + (print_appelli[i][4])[0:10] 
            except:
                print("Empty array ") #da cancellare era solo per debug
        update.message.reply_text(lista_appelli, parse_mode='Markdown')
    
    #print grades' average
    if choice == 'Media':
        try:
            media = LIUC.get_media(username1, password)[0]
            voto = LIUC.get_media(username1, password)[1]
            return_media_voto = "La tua media è *" + str(media) + "*, il voto di laurea è *" + str(voto)[0:5] + "*. " + thumbs_up_emoji
            update.message.reply_text(return_media_voto, parse_mode='Markdown')
        except:
            #da fixare, problema in liucAPI, probabilmente se logga due volte va a cazzo
            update.message.reply_text("Impossibile trovare media, riprova. ")


    #print uni taxes
    if choice == 'Tasse':
        tasse_info = LIUC.get_tasse(username1, password)
        pagato = sum(tasse_info[1])
        da_pagare = tasse_info[0]
        tasse_message = ""
        tasse_link = ""
        url_stampa_tasse = 'sol.liuc.it/esse3/auth/studente/Tasse/StampaMav.do?fatt_id='

        if len(da_pagare) == 0:
            tasse_message = "Non hai tasse da pagare! \nHai pagato: *€" + pagato + "*in tutto. "     
        else:
            for i in range(len(da_pagare)):
                tasse_message = tasse_message +  str(i+1) + ") *€" + str(da_pagare[i][0]) + "* entro il *" + str(da_pagare[i][1] +"*\n")
                tasse_link = "Link tassa: " + str(url_stampa_tasse) + "" + str(da_pagare[i][2]) +  "\n"

        update.message.reply_text(tasse_message, parse_mode='Markdown')  
        #uncomment this to send link to pdf with payment details
        #update.message.reply_text(tasse_link)  
        LIUC.get_mav_pdf(username1, password, da_pagare[0][2])
        pdf_path = '/tmp/' + username1.replace("." , "") + ".pdf"
        update.message.reply_document(document=open(pdf_path, 'rb'))

    
    #stop the conversation
    if choice == 'Chiudi':
        update.message.reply_text("Logout effettuato! Scrivi /start per ricominciare!")
        return ConversationHandler.END


    reply_keyboard = [['Esiti', 'Libretto', 'Appelli', 'Media', 'Tasse', 'Chiudi']]
    update.message.reply_text(
    "    Scegli un'opzione    ",
    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ACTIVITIES




#main bot function to handle the conversation
def main() -> None:
    
    updater = Updater("1492190157:AAHJKgrfxnxFKodOWleARo3hte3DBvuHYyA", use_context=True)
    dispatcher = updater.dispatcher


    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOGIN: [MessageHandler(Filters.regex('^(Login)$'), login, pass_user_data=True)],
            INSERT_USER: [MessageHandler(Filters.text, insert_user, pass_user_data=True)],
            INSERT_PASSWORD: [
                MessageHandler(Filters.text, insert_password, pass_user_data=True)],
            ACTIVITIES: [MessageHandler(Filters.regex('^(Esiti|Libretto|Appelli|Media|Tasse|Chiudi)$'), activities)],
        },
        fallbacks=[CommandHandler('cancel', activities)],
         allow_reentry = True,
    )

    dispatcher.add_handler(conv_handler)

    #starting bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


