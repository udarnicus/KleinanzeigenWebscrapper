import requests
from bs4 import BeautifulSoup
from matplotlib import pyplot
import numpy as np
import csv
import os

cars = [("Kia Picanto", 13200, 15), ("Renault Twingo", 20700, 38), ("Hyundai I10", 11600, 31), ("Citroen C1", 5900, 7),
        ("Peugeot 107", 19300, 5), ("Toyota Aygo", 24100, 5), ("Toyota IQ", 24100, 41),
        ("Mitsubishi Space Star", 17700, 28), ("Renault Clio", 20700, 6), ("Smart ForTwo",23000,4), ("Mazda 2", 16800,3), ("Ford Fiesta",9000,19)
    ,("Suzuki Swift",23600,19),("Opel Corsa",19000,10) ("Chevrolet Spark")]

jahr = []
km = []
preis = []
kmsections = [19999,39999,59999,79999,99999,119999,139999,159999,179999,199999,219999]
yearsMedian = []


minMileage = 1
maxMileage = 220000
minPreis = 500
maxPreis = 6000
minRegistration = "01-01-2004"
maxRegistration = "01-01-2020"

def autolabel(rects):

    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., height + 1,
                '%.1f' % float(height),
                ha='center', va='bottom',fontsize=5)


def getElements(page,carID,modellID):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}
    link = "https://suchen.mobile.de/fahrzeuge/search.html?damageUnrepaired=NO_DAMAGE_UNREPAIRED&isSearchRequest=true&makeModelVariant1.makeId={}&makeModelVariant1.modelId={}" \
           "&minMileage={}&maxMileage={}&minPrice={}&maxPrice={}&minFirstRegistrationDate={}&maxFirstRegistrationDate={}&pageNumber={}&scopeId=C&sfmr=false&sortOption.sortBy=creationTime&sortOption.sortOrder=DESCENDING".format(
        str(carID), str(modellID), str(minMileage), maxMileage, minPreis, maxPreis, minRegistration, maxRegistration,
        page)
    soup = BeautifulSoup(requests.get(link, headers=headers).text, "html.parser")
    nonBreakSpace = u'\xa0'
    # soup.replace(u'\xa0',' ')
    # print(soup.prettify())
    # print(soup)
    elements = soup.find_all(class_="cBox-body--resultitem")

    for element in elements:
        price = int(element.find(class_="price-block").span.string.split(u'\xa0')[0].replace(".", ""))
        kilometer = int(
            element.find(class_="vehicle-data--ad-with-price-rating-label").find_all("div")[0].string.split(",")[
                1].replace(u'\xa0', " ").split(' ')[1].replace(".", ""))
        year = int(element.find(class_="vehicle-data--ad-with-price-rating-label").find_all("div")[0].string.split(",")[
                       0].split(" ")[1].split("/")[1])

        jahr.append(year)
        km.append(kilometer)
        preis.append(price)

for car in cars:
    if not os.path.exists('./CarsData/' + car[0]):
        os.makedirs('./CarsData/' + car[0])

    jahr = []
    km = []
    preis = []
    yearsMedian = []

    for page in range(30):
        getElements(page + 1,car[1],car[2])

    pyplot.scatter(preis, km)
    pyplot.xlabel("Preis")
    pyplot.ylabel("Kilometerstand")
    pyplot.title("Verhältnis Preis Kilometerstand " + car[0])
    pyplot.savefig("./CarsData/" + car[0] + "/PreisKmScatter.png")
    pyplot.close()
    #pyplot.show()

    pyplot.hist2d(preis, km, bins=50, cmap="Blues")
    pyplot.title("Verhältnis Preis Kilometerstand Histogram " + car[0])
    pyplot.xlabel("Preis")
    pyplot.ylabel("Kilometerstand")
    cb = pyplot.colorbar()
    cb.set_label("accumulation of prices")
    pyplot.savefig("./CarsData/" + car[0] + "/PreisKmHistogram.png")
    pyplot.close()
    #pyplot.show()

    pyplot.scatter(jahr, preis)
    pyplot.xlabel("Baujahr")
    pyplot.ylabel("Preis")
    pyplot.title("Verhältnis Preis Baujahr " + car[0])
    pyplot.savefig("./CarsData/" + car[0] + "/PreisBaujahrScatter.png")
    pyplot.close()
    #pyplot.show()

    pyplot.hist2d(jahr, preis, bins=20, cmap="Blues")
    cb1 = pyplot.colorbar()
    cb1.set_label("accumulation of prices")
    pyplot.xlabel("Baujahr")
    pyplot.ylabel("Preis")
    pyplot.title("Verhältnis Preis Baujahr Histogram " + car[0])
    pyplot.savefig("./CarsData/" + car[0] + "/PreisBaujahrHistogram.png")
    pyplot.close()
    #pyplot.show()

    years = list(set(jahr))
    years.sort()

    numberOfProbes = []
    for year in years:
        numberOfProbes.append(
            "Number of Prices for " + str(year) + " : " + str(len([p for j, p in zip(jahr, preis) if j == year])))

    with open('./CarsData/' + car[0] + '/numberOfProbesproJahr.csv', mode='w', newline='') as productsFile:
        employee_writer = csv.writer(productsFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for string in numberOfProbes:
            employee_writer.writerow(string)

    numberOfProbeskm = []
    for kilometer in kmsections:
        numberOfProbeskm.append("Number of Prices for < then " + str(kilometer+1) + " are : " + str(len([p for p in km if kilometer - 20000 < p < kilometer])))

    with open('./CarsData/' + car[0] + '/numberOfProbesproKilometerstand.csv', mode='w', newline='') as productsFile:
        employee_writer = csv.writer(productsFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for string in numberOfProbeskm:
            employee_writer.writerow(string)


    for year in years:
        yearsMedian.append(np.mean([p for j, p in zip(jahr, preis) if j == year]))

    yearsPercentile = []
    for year in years:
        arr = [p for j, p in zip(jahr, preis) if j == year]
        if not arr:
            arr = [0]
        yearsPercentile.append(np.percentile(arr, 10))

    fig = pyplot.figure()
    ax = fig.add_subplot(111)
    ind = np.array(years)
    #ind = np.arange(len(years)) + min(years)
    width = 0.4
    rects = ax.bar(ind, yearsMedian, width, color="blue", align="center")
    rects2 = ax.bar(ind + 0.4, yearsPercentile, width, color="red", align="center")
    ax.legend(labels=['Durchschnitt', "10% Percentile"])
    pyplot.title("Durchschnitt Preis pro Jahr und Percentile " + car[0])
    pyplot.xlabel('Jahr')
    pyplot.ylabel('Preis in €')

    autolabel(rects)
    pyplot.savefig("./CarsData/" + car[0] + "/DurchschnittPreisBaujahr.png")
    pyplot.close()
    #pyplot.show()

    kmAverage = []
    for kilometer in kmsections:
        kmAverage.append(np.mean([p for k, p in zip(km, preis) if kilometer - 20000 < k < kilometer]))

    kmPercentile = []
    for kilometer in kmsections:
        arr = [p for k, p in zip(km, preis) if kilometer - 20000 < k < kilometer]
        if not arr:
            arr = [0]
        kmPercentile.append(np.percentile(arr,10))

    fig1 = pyplot.figure()
    ax1 = fig1.add_subplot(111)
    ax1.hist(kmsections,
                         bins=[0, 20000, 40000, 60000, 80000, 100000, 120000, 140000, 160000, 180000, 200000,
                               220000], weights=kmAverage)
    ax1.hist(kmsections,
             bins=[0, 20000, 40000, 60000, 80000, 100000, 120000, 140000, 160000, 180000, 200000,
                   220000], weights=kmPercentile,color="red")
    ax1.legend(labels=['Durchschnitt', "10% Percentile"])
    pyplot.title("Durchschnitt Preis für Kilometerstand " + car[0])
    pyplot.xlabel('KM')
    pyplot.ylabel('Preis in €')
    pyplot.savefig("./CarsData/" + car[0] + "/DurchschnittPreisKilometerstand.png")
    pyplot.close()
    #pyplot.show()

# kmAverage = []
# for kilometer in kmsections:
#     kmAverage.append(np.mean([p for k, p in zip(km, preis) if kilometer - 20000 < k < kilometer]))
#
# kmPercentile = []
# for kilometer in kmsections:
#     kmPercentile.append(np.percentile([p for k, p in zip(km, preis) if kilometer - 20000 < k < kilometer],10))
#
#
# fig = pyplot.figure()
# ax = fig.add_subplot(111)
#
# ind = np.arange(start=20000,stop=200000,step=20000)
# np.append(ind,500000)
# width = 0.4
# rects = ax.bar(ind,kmAverage,width,color="blue",align="center")
# rects2 = ax.bar(ind + 0.4,kmPercentile,width,color="red",align="center")
# ax.legend(labels=['Durchschnitt',"10% Percentile"])
# pyplot.title("Durchschnitt Preis pro für KM")
# pyplot.ylabel('Km')
# pyplot.ylabel('Preis in €')
#
# autolabel(rects)
#
# pyplot.show()


#pyplot.bar(years,yearsMedian,align="center",alpha=0.6)
#pyplot.show()



#pyplot.hist(jahr,bins=preis.sort())
#pyplot.show()


# fig = pyplot.figure()
# ax = Axes3D(fig)
# ax.scatter(jahr,km,preis)
# pyplot.show()

# pointCloud = pv.PolyData(points)
# print(np.allclose(points, pointCloud.points))
# #pointCloud.plot(render_points_as_spheres=True)
#
# plotter = pv.Plotter()
# plotter.add_mesh(pointCloud,color='maroon', point_size=10.,
#                  render_points_as_spheres=True)
#
# plotter.show_grid()
# plotter.show()
