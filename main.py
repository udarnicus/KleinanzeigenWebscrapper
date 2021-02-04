import os
import statistics
from bs4 import BeautifulSoup
import csv

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#from pyvirtualdisplay import Display
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
bot_token = "1324960290:AAF5RzbyAHY1m0pAH8AKkC9ascP2rZsSPic"
# ("laptop rtx",1,650,0) ,  ("gaming laptop",1,550,0)
carsList = []  # last parameter in der Nähe - 0=everywhere, 1=30kmradius
queueOfSeenProducts = Queue()
js_string = "var element = document.getElementById('gdpr-banner');element.remove();"
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


def fillProductList():
    global cur
    global carsList
    productList = []
    cur.execute("SELECT Name,Untergrenze,Obergrenze,Reichweite FROM Suche")
    for Name, Untergrenze, Obergrenze, Reichweite in cur:
        productList.append((Name, Untergrenze, Obergrenze, Reichweite))


def checkIfSearchOrBroken(element):
    #title = element.find_element_by_class_name("aditem").find_element_by_class_name("aditem-main").find_element_by_class_name("ellipsis").text
    title = element.find(class_="aditem").find(class_="aditem-main").find(class_="ellipsis").string
    title = title.lower()
    title = title.split()
    if "suche" in title:
        return True
    if "defekt" in title:
        return True
    return False


def initialize():
    option = webdriver.ChromeOptions()

    chrome_prefs = {}
    option.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}

    #option.add_argument("headless")

    global driver


    path = os.path.join(os.getcwd(), "chromedriver.exe")
    driver = webdriver.Chrome(path, options=option)


    driver.get('https://www.ebay-kleinanzeigen.de/')
    # driver.save_screenshot('SeleniumChromiumTest.png')


def telegram_send_message(message):
    bot_link = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatid + '&parse_mode=Markdown&text=' + message
    return requests.get(bot_link)


def getLinkOfElement(element):
    return element.find(class_="aditem").find(class_="aditem-main").find(class_="ellipsis")["href"]


def getElements(product, nearby):

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}
    if nearby:
        link = "https://www.ebay-kleinanzeigen.de/s-sindelfingen/" + product.replace(" ", "-") + "/k0l8991r30"
    else:
        link = "https://www.ebay-kleinanzeigen.de/s-" + product.replace(" ", "-") + "/k0"
    soup = BeautifulSoup(requests.get(link,headers = headers).text,"html.parser")
    elements = soup.find_all(class_="lazyload-item")
    return elements


def filterElementsAndAddToListAndNotify(lowerLimit, upperLimit, listOfElements):
    for element in listOfElements:
        price = element.find(class_="aditem").find(class_="aditem-details").strong.string

        elementID = element.find(class_="aditem")["data-adid"]
        if not price:
            price = "0"
        # print("Price:"  + price)
        price = price.split()[0].replace(".", "")
        if price.isnumeric():
            price = int(price)
            if lowerLimit < price < upperLimit:
                if not checkIfSearchOrBroken(element):

                    if not checkIfProductAlreadySeen(elementID):

                        if queueOfSeenProducts.qsize() < maxQueueSize:
                            queueOfSeenProducts.put((elementID,price))
                        else:
                            queueOfSeenProducts.get()
                            queueOfSeenProducts.put((elementID,price))
                        link = getLinkOfElement(element)
                        bot.sendMessage(bot_chatid, str("*Price:" + str(price) + "*" + "  https://www.ebay-kleinanzeigen.de/" + link),
                                        parse_mode="Markdown")


def checkIfProductAlreadySeen(elementID):
    if(queueOfSeenProducts.qsize() ==0):
        return False
    for product in list(queueOfSeenProducts.queue):
        if(product[0] == elementID):
            return True
    return False


def checkAndRemoveBanner(driver):
    banner = driver.find_element_by_id('gdpr-banner')
    if banner is not None:
        driver.execute_script(js_string)
        print("Banner Deleted!")


def handle(msg):
    command = msg['text']
    if command == "/status":
        bot.sendMessage(bot_chatid, str("*Still running* :)"), parse_mode="Markdown")
    if command == "/stop":
        sys.exit()
    if command == "/products":
        bot.sendMessage(bot_chatid, str(carsList), parse_mode="Markdown")

def writeAlreadySeenProductsToCSV():
    with open('alreadySeenProducts.csv', mode='w',newline='') as productsFile:
        employee_writer = csv.writer(productsFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for product in list(queueOfSeenProducts.queue):
            employee_writer.writerow([product[0],product[1]])
        #employee_writer.writerow(['John Smith', 'Accounting', 'November'])
        #employee_writer.writerow(['Erica Meyers', 'IT', 'March'])

def readAlreadySeenProductsToCSV():
    try:
        with open('alreadySeenProducts.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')

            for row in csv_reader:
                print(row)
                queueOfSeenProducts.put((row[0],row[1]))
    except FileNotFoundError:
        print("No stored products available")



def mainFunction():
    global starttime
    global endtime

    connectToDataBase()
    fillProductList()
    readAlreadySeenProductsToCSV()
    print(queueOfSeenProducts)
    while True:
        try:
            # MessageLoop(bot, handle).run_as_thread()
            print("Test")

            while True:
                media = []

                for product in carsList:
                    start = time.time()
                    elements = getElements(product[0], product[3])
                    t = threading.Thread(target=filterElementsAndAddToListAndNotify,args=(product[1], product[2], elements))
                    t.start()
                    #filterElementsAndAddToListAndNotify(product[1], product[2], elements)
                    end = time.time()
                    media.append(end-start)
                    print(str(end - start))
                    print(list(queueOfSeenProducts.queue))
                s = time.time()
                writeAlreadySeenProductsToCSV()
                m = time.time()
                print("Time fo writing to txt file: " + str(m-s))
                #print(listOfPrices)
                print("Average needed: " + str(statistics.mean(media)))

                print("Waiting...")

                fillProductList()
                time.sleep(60)
        except Exception as e:
                #driver.quit()
                print("System Crashed" + str(e))



bot = telepot.Bot(bot_token)
thread = threading.Thread(target=MessageLoop(bot, handle).run_as_thread(relax=10, timeout=100), daemon=True)
thread.start()
mainFunction()


