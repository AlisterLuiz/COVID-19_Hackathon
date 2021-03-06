from django.shortcuts import render
import pyrebase
from googleplaces import GooglePlaces, types, lang
import random
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
import geocoder
import json
from django.conf import settings
import os
# from cart.cart import Cart
# from myproducts.models import Product

g = geocoder.ip('me')
lat = g.latlng[0]
lng = g.latlng[1]


config = {
    "apiKey": "AIzaSyBk3hKgOO2SrqosNhsmipgEzi_tHQ921lE",
    "authDomain": "covid-19-85e6d.firebaseapp.com",
    "databaseURL": "https://covid-19-85e6d.firebaseio.com",
    "storageBucket": "covid-19-85e6d.appspot.com",
    "serviceAccount": os.path.join(settings.BASE_DIR, "essentials_app/covid.json")
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

# Create your views here.


class HomePageView(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'index.html')

class ShopCart(TemplateView):
    def get(self, request, **kwargs):
        json_file = "cart.json"
        data = read_json_file(json_file)
        print(type(data["items"]))
        return render(request, 'cart.html', {
            'data': data["items"],
        })

class ShopPageCategory(TemplateView):
    def get(self, request, **kwargs):
        default_radius = 1000
        category = kwargs["category"]
        data = matchData(default_radius, category)
        return render(request, 'shops/browse.html', {
            'shops': data,
            'category': category,
            'radius': default_radius
        })
    def post(self, request, **kwargs):
        # x = insertData(request)
        data = matchData(request.POST["radius"], request.POST["type"])
        return render(request, 'shops/browse.html', {
            'shops': data,
            'category': request.POST["type"],
            'radius': request.POST["radius"]
        })


class AdminPageView(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'shops/admin.html')
    
class ShopPageView(TemplateView):
    def get(self, request, **kwargs):
        print(kwargs)
        category = kwargs["category"]
        shopId = kwargs["shopId"]
        json_file = "grocery.json" if category.lower() == "supermarket" else "pharmacy.json"
        name = "AL SAAH FLOUR MILL" if category.lower() == "supermarket" else "AL MARWAH PHARMACY LLC"
        vicinity = "Al Mina Road, Sharjah" if category.lower() == "supermarket" else "Shop no. 1-2, Mister Baker building, Al Qasmia Street Opposite Home Box"
        print(json_file)
        data = read_json_file(json_file)
        print(type(data))
        return render(request, 'shops/read.html', {
            'category' : category,
            'shopId' : shopId,
            'name' : name,
            "vicinity" : vicinity,
            "occupancy" : 9,
            'data' : data["items"],
            'map_link' : data["url"]
        })


class AboutPageView(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'shops/browse.html', context=None)


def matchData(radius, category):
    google_places = GooglePlaces("AIzaSyDb5kEEULH5xs30Beq-dsKnQqbsdjX6AKI")

    if (category.upper() == "SUPERMARKET"):
        t = [types.TYPE_GROCERY_OR_SUPERMARKET]
    else:
        t = [types.TYPE_PHARMACY]

    query_result = google_places.nearby_search(
        lat_lng={'lat': lat, 'lng': lng},
        radius=int(radius),
        types=t)

    checkResult = query_result.raw_response["results"]
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print(checkResult)

    db_results = db.child("entities").get().val()

    dt = dict(db_results)
    lt = list(dt.values())
    result = filter(lambda x: x["type"] == category.upper(), lt)
    result = list(result)

    newList = []

    print(result[0]["id"])
    print("======================")
    print(checkResult[0]["id"])
    print("======================")

    for r1 in result:
        for r2 in checkResult:
            if(r1["id"] == r2["id"]):
                r1["available"] = r1["occupancy"] - r1["occupied"]
                r1["distance"] = random.choice(["1.0", "0.5", "0.85", "2.0", "1.3", "1.74"])
                newList.append(r1)

                break

    print("#######################")
    print(newList)

    return newList


def insertData(request):

    google_places = GooglePlaces("AIzaSyDb5kEEULH5xs30Beq-dsKnQqbsdjX6AKI")

    query_result = google_places.nearby_search(
        lat_lng={'lat': 25.3526878, 'lng': 55.3836953},
        radius=500,
        # types=[types.TYPE_GROCERY_OR_SUPERMARKET])
        types=[types.TYPE_PHARMACY])
    x = 0

    places = []

    for place in query_result.raw_response["results"]:
        x = x+1
        print(x)
        print("*****")
        if x % 1 == 0:
            obj = dict()
            obj["id"] = place["id"]
            obj["location"] = str(place["geometry"]["location"])
            obj["name"] = place["name"]
            obj["vicinity"] = place["vicinity"]
            obj["openTill"] = random.choice(
                ["08:00", "09:00", "10:00", "11:00", "00:00", "01:00"])
            obj["occupancy"] = random.randint(3, 15)
            obj["placeID"] = place["place_id"]
            obj["occupied"] = random.randint(
                obj["occupancy"]-4, obj["occupancy"])
            obj["pickup"] = random.choice([True, False])
            obj["homeDelivery"] = random.choice([True, False])
            obj["type"] = "PHARMACY"
            # obj["type"] = "GROCERY"

            places.append(obj)

    for place in places:
        print("========================")
        print(place)
        db.child("entities").push(place)
        return True

def read_json_file(json_file):
    json_data = open(os.path.join(settings.BASE_DIR, "essentials_app/", json_file))
    json_data = json.load(json_data)
    return json_data
