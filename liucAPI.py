import requests
import json 
from lxml import html
from lxml import etree
from bs4 import BeautifulSoup
import time
import numpy
import getpass 
import os
clear = lambda: os.system('cls')
import json

""" 
Most of these functions work through REST APIs, but due to lack of documentation about some features,
this script uses also HTTP request scraping (for example in def get_last_mark()) 
this is the cause for having two functions for logging in, liucLogin() for loggin through http requests
while login() for logging through REST APIs
further investigation in APIs documentation should fix this and make the script work ONLY through REST API. 
Function get_last_mark() works through http scraping, and it requires liucLogin()
Please note that the script is working only with students' account. """

#not all urls are from official REST API's endpoints
url_login = "https://sol.liuc.it/esse3/auth/Logon.do"
url_esiti = 'https://sol.liuc.it/esse3/auth/studente/Appelli/BachecaEsiti.do'
url_appelli = 'https://sol.liuc.it/e3rest/api/calesa-service-v1/appelli/'
url_login_end = "https://sol.liuc.it/e3rest/api/login/"
#average endpoint = url_average + matId (get this from login()) + "/medie"
url_average = 'http://sol.liuc.it/e3rest/api/libretto-service-v2/libretti/'
#example: ".../e3rest/api/libretto-service-v2/libretti/999/medie" return average of student with matId 999
url_libretto = 'http://sol.liuc.it/e3rest/api/libretto-service-v2/libretti/'
url_tasse = 'http://sol.liuc.it/e3rest/api/tasse-service-v1/lista-fatture?persId='

#start requests session
session = requests.session()
session.get(url_login)

#login through API
#return basic info about the student
def login(username1, pwd):
    response = session.get(url_login_end, auth=(username1, pwd))
    user_details_json = json.loads(response.text)
    user_details = []
    matId = (user_details_json["user"]["trattiCarriera"][0]["matId"])
    stuId = (user_details_json["user"]["trattiCarriera"][0]["stuId"])
    matricola = (user_details_json["user"]["trattiCarriera"][0]["matricola"])
    name = (user_details_json["user"]["firstName"])
    surname = (user_details_json["user"]["lastName"])
    personaId = (user_details_json["user"]["persId"])
    user_details.append(matId)
    user_details.append(stuId)
    user_details.append(matricola)
    user_details.append(name)
    user_details.append(surname)
    user_details.append(personaId)
    return user_details



#return a matrix with available exams and their details
#this function works through JSON REST API
def getAppelli(username1, pwd):
    appelli = session.get(url_appelli, auth=(username1, pwd))
    appelli_json = json.loads(appelli.text)
    appelli_detail = [[]]
    advanced_details_exam = [[]]
    #look for exam attributes, so i can search for exams description
    #first endpoints = exam id
    #second endopoints = input(exam_id)->output(exam_details)
    for i in range(len(appelli_json)):
        id_appello = appelli_json[i]["adDefAppId"]
        id_corso = appelli_json[i]["cdsDefAppId"]
        desc_appello = appelli_json[i]["adDes"]
        appelli_detail.insert(i, [desc_appello, id_appello, id_corso])
        
    #look for exam details, giving as input exam id 
    for i in range(len(appelli_detail) - 1):
        detail_endpoints = url_appelli + str(appelli_detail[i][2]) + "/" +  str(appelli_detail[i][1])
        get_exam_info = session.get(detail_endpoints, auth=(username1, pwd))
        exam_info_json = json.loads(get_exam_info.text) 
        """ print(exam_info_json)
        print(detail_endpoints) """

        for j in range(len(exam_info_json) - 1):
            corso = exam_info_json[j]["adDes"]
            data_appello = exam_info_json[j]["dataInizioApp"]
            data_inizio = exam_info_json[j]["dataInizioIscr"]
            data_fine = exam_info_json[j]["dataFineIscr"]
            tipo_appello = exam_info_json[j]["desApp"]
            advanced_details_exam.insert((j+i), [corso, data_appello, tipo_appello, data_inizio, data_fine])

    return advanced_details_exam


#return average and most likely graduation grade
def get_media(username1, pwd):
    matricola_id = login(username1, pwd)[0]
    personal_url_average = url_average + str(matricola_id) + "/medie"
    getAverage = session.get(personal_url_average, auth=(username1,pwd))
    average_json = json.loads(getAverage.text)
    average = average_json[1]["media"]
    votolaurea = average_json[3]["media"]
    return average, votolaurea



#return a matrix in which each line contains [exam name, exam grade]
#if an exam has not a grade, return [exam name, "---"]
def get_libretto(username1, pwd):
    libretto = [[]]
    matricola_id = login(username1, pwd)[0]
    personal_url_libretto = url_libretto + str(matricola_id) + "/righe/"
    response = session.get(personal_url_libretto, auth = (username1, pwd))
    libretto_json = json.loads(response.text)
    num_esami_da_dare = 0
    for i in range(len(libretto_json)):
        
        esame_libretto = libretto_json[i]["adDes"]
        voto_libretto = libretto_json[i]["esito"]["voto"]
        if voto_libretto == None:
            voto_libretto = "---"
            num_esami_da_dare = num_esami_da_dare + 1
        libretto.insert(i, [esame_libretto, voto_libretto])

    #adding info about how many exam are finished
    num_esami_dati = len(libretto_json) - num_esami_da_dare
    #insert the info in last line of the list
    esami_dati_da_dare = [num_esami_dati, num_esami_da_dare]

    return libretto, esami_dati_da_dare
    

def get_tasse(username1, pwd):
    persId = login(username1, pwd)[5]
    personal_url_tax = url_tasse + str(persId)
    response = session.get(personal_url_tax, auth = (username1, pwd))
    tax_json = json.loads(response.text)
    tasse_da_pagare = []
    tasse_pagate = []
    for i in range(len(tax_json)):
        if tax_json[i]["importoPag"] != None:
            tasse_pagate.append(tax_json[i]["importoPag"])
        else:
            tasse_da_pagare.append([tax_json[i]["importoFattura"],tax_json[i]["scadFattura"],tax_json[i]["fattId"]])
    
    return tasse_da_pagare, tasse_pagate

#----------------------------------------------------------------------------------------------------------------

def liucLogin(username1, pwd):
    response = session.get(url_login, auth=(username1, pwd))
    #salvo la pagina di scelta carriera
    tree = etree.HTML(response.text)
    element = tree.xpath('//*[@id="gu_toolbar_sceltacarriera"]')
    try:
        content = etree.tostring(element[0])
        url1 = content[108:113].decode('utf-8')
        print("Accedo all'ultima carriera disponibile...") 
        url_carriera = "https://sol.liuc.it/esse3/auth/studente/SceltaCarrieraStudente.do?stu_id=" + url1
        response = session.get(url_carriera, auth=(username1, pwd))
        if (response.status_code) == 200:
            print("Login riuscito. ") 
        else:
            print("Login non riuscito. ")
    except:
        print("Login non riuscito ")



#check the last grades
def get_last_mark(username1, pwd):
    response = session.get(url_esiti, auth=(username1,pwd))
    html_esiti = BeautifulSoup(response.text, "html.parser")

    #nome deve essere fixato, non trovo il css selector esatto, non funziona neanche con xpath
    #controllare documentazione e3rest su esse3 per api json
    prof_esame_esito = html_esiti.select('td.detail_table:nth-child(3)')
    data_esame_esito = html_esiti.select('td.detail_table:nth-child(1)')
    voto_esame_esito = html_esiti.select('td.detail_table:nth-child(5) > form:nth-child(1)')
    print(len(prof_esame_esito))
    esiti = []
    quanti_esiti = len(prof_esame_esito)

    for i in range(quanti_esiti):
        prof_esame_esito1 = prof_esame_esito[i].get_text()
        data_esame_esito1 = data_esame_esito[i].get_text()
        voto_esame_esito1 = voto_esame_esito[i].get_text()
        info_esito = prof_esame_esito1 + " - " + data_esame_esito1 + " - " + voto_esame_esito1
        info_esito = info_esito.replace("\n", "")
        esiti.append(info_esito)
  
    return esiti