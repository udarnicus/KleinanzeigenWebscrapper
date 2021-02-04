import os
import statistics
from bs4 import BeautifulSoup
import csv

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
# from pyvirtualdisplay import Display
import selenium
from queue import Queue
import telepot  # Importing the telepot library
from selenium.webdriver.support.wait import WebDriverWait
from telepot.loop import MessageLoop  # Library function to communicate with telegram bot
import requests
import threading
import time
import sys
import mariadb

location = "71063 Sindelfingen"
bot_chatid = "1219874561"
bot_token = "1530637349:AAFUsf-NyvVKbeJXQQUj2K_pDs58_-VSrYo"
# ("laptop rtx",1,650,0) ,  ("gaming laptop",1,550,0)
carsList = []  # last parameter in der Nähe - 0=everywhere, 1=30kmradius
queueOfSeenCars = Queue()
driver = None
maxQueueSize = 100
cur = None

starttime = None
endtime = None


def connectToDataBase():
    global cur
    connection = mariadb.connect(
        user="root",
        password="incorrect",
        host="192.168.0.200",
        port=3306,
        database="kleinanzeigen")
    cur = connection.cursor()


def fillCarsList():
    global cur
    global carsList
    carsList = []
    cur.execute("SELECT Name,CarID,ModellID,minMileage,maxMileage,minPreis,maxPreis,minRegistration,maxRegistration FROM SucheAutos")
    for Name, CarID, ModellID, minMileage, maxMileage, minPreis, maxPreis, minRegistration, maxRegistration in cur:
        carsList.append((Name, CarID, ModellID, minMileage, maxMileage, minPreis, maxPreis, minRegistration,maxRegistration))


# def checkIfSearchOrBroken(element):
#     #title = element.find_element_by_class_name("aditem").find_element_by_class_name("aditem-main").find_element_by_class_name("ellipsis").text
#     title = element.find(class_="aditem").find(class_="aditem-main").find(class_="ellipsis").string
#     title = title.lower()
#     title = title.split()
#     if "suche" in title:
#         return True
#     if "defekt" in title:
#         return True
#     return False


def telegram_send_message(message):
    bot_link = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatid + '&parse_mode=Markdown&text=' + message
    return requests.get(bot_link)


def getDescriptionOfCar(element):
    description = element.find(class_="vehicle-data--ad-with-price-rating-label")
    firstrow = description.find_all("div")[0].string
    secondrow = description.find_all("div")[1].text

    print("FirstRow:" + firstrow)
    print("SecondRow:" + secondrow)
    return "\n <b>" + firstrow + " \n " + secondrow + "</b> \n "


def getElements(carId, modellID,minMileage,maxMileage,minPreis,maxPreis,minRegistration,maxRegistration):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}
    link = "https://suchen.mobile.de/fahrzeuge/search.html?damageUnrepaired=NO_DAMAGE_UNREPAIRED&isSearchRequest=true&makeModelVariant1.makeId={}&makeModelVariant1.modelId={}" \
           "&minMileage={}&maxMileage={}&minPrice={}&maxPrice={}&minFirstRegistrationDate={}&maxFirstRegistrationDate={}&scopeId=C&sfmr=false&sortOption.sortBy=creationTime&sortOption.sortOrder=DESCENDING".format(
        str(carId), str(modellID), str(minMileage), maxMileage, minPreis, maxPreis, minRegistration,maxRegistration)
    soup = BeautifulSoup(requests.get(link, headers=headers).text, "html.parser")
    # print(soup)
    elements = soup.find_all(class_="cBox-body--resultitem")
    return elements


def filterElementsAndAddToListAndNotify(listOfElements):
    for element in listOfElements:
        price = element.find(class_="price-block").span.string

        elementID = element.a["data-ad-id"]
        if not price:
            price = "0"
        # print("Price:"  + price)
        price = price.split()[0].replace(".", "")
        if price.isnumeric():
            price = int(price)
            # if not checkIfSearchOrBroken(element):
            if not checkIfProductAlreadySeen(elementID):

                if queueOfSeenCars.qsize() < maxQueueSize:
                    queueOfSeenCars.put((elementID, price))
                else:
                    queueOfSeenCars.get()
                    queueOfSeenCars.put((elementID, price))
                link = element.a["href"]
                description = getDescriptionOfCar(element)
                rating = element.find(class_="mde-price-rating__badge__label mde-price-rating__badge__label--right").string
                if (element.find(class_="img-responsive") != None):
                    img = element.find(class_="img-responsive")["data-src"].replace("//", "")
                else:
                    img = ""
                print(img)
                bot.sendMessage(bot_chatid, str(
                    '<a href="{}">-</a> <b>Price: {}€   {}</b>                                                    '
                    '\n {} \n'
                    '<a href="{}">#####Go to Car#####</a>'.format(img, price, rating, description, link)),
                                parse_mode="HTML")
                # bot.sendMessage(bot_chatid,'<a href="{}">.</a>'.format(img),parse_mode="HTML")


def checkIfProductAlreadySeen(elementID):
    if (queueOfSeenCars.qsize() == 0):
        return False
    for product in list(queueOfSeenCars.queue):
        if (product[0] == elementID):
            return True
    return False


def handle(msg):
    command = msg['text']
    if command == "/status":
        bot.sendMessage(bot_chatid, str("*Still running* :)"), parse_mode="Markdown")
    # if command == "/stop":
    #     sys.exit()
    if command == "/products":
        bot.sendMessage(bot_chatid, str(carsList), parse_mode="Markdown")


def writeAlreadySeenCarsToCSV():
    with open('alreadySeenCars.csv', mode='w', newline='') as productsFile:
        employee_writer = csv.writer(productsFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for car in list(queueOfSeenCars.queue):
            employee_writer.writerow([car[0], car[1]])
        # employee_writer.writerow(['John Smith', 'Accounting', 'November'])
        # employee_writer.writerow(['Erica Meyers', 'IT', 'March'])


def readAlreadySeenCarsToCSV():
    try:
        with open('alreadySeenCars.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')

            for row in csv_reader:
                print(row)
                queueOfSeenCars.put((row[0], row[1]))
    except FileNotFoundError:
        print("No stored products available")


def mainFunction():
    global starttime
    global endtime

    connectToDataBase()
    fillCarsList()
    readAlreadySeenCarsToCSV()
    print(queueOfSeenCars)
    while True:
        try:
            # MessageLoop(bot, handle).run_as_thread()
            print("Test")

            while True:
                media = []

                for car in carsList:
                    start = time.time()
                    elements = getElements(car[1], car[2], car[3], car[4], car[5], car[6], car[7], car[8])
                    t = threading.Thread(target=filterElementsAndAddToListAndNotify(elements))
                    t.start()
                    # filterElementsAndAddToListAndNotify(product[1], product[2], elements)
                    end = time.time()
                    media.append(end - start)
                    print(str(end - start))
                    print(list(queueOfSeenCars.queue))
                writeAlreadySeenCarsToCSV()

                print("Average needed: " + str(statistics.mean(media)))

                print("Waiting...")

                fillCarsList()
                time.sleep(60)
        except Exception as e:
            # driver.quit()
            print("System Crashed" + str(e))


bot = telepot.Bot(bot_token)
thread = threading.Thread(target=MessageLoop(bot, handle).run_as_thread(relax=10, timeout=100), daemon=True)
thread.start()
mainFunction()
