from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
from .models import CarDealer, CarMake, CarModel
# from .restapis import related methods
from .restapis import get_request, get_dealers_from_cf, get_dealer_reviews_from_cf, get_dealers_by_state, get_dealer_by_id, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/login.html', context)
    else:
        return render(request, 'djangoapp/login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://eu-de.functions.appdomain.cloud/api/v1/web/kvothe_dev/dealership-package/get-dealership"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        context["dealership_list"] = dealerships
        # Return a list of dealer short name
        # Concat all dealer's short name
        #dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        #return HttpResponse(dealer_names)
        return render(request, 'djangoapp/index.html', context)

# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        context = {}

        url = "https://eu-de.functions.appdomain.cloud/api/v1/web/OpentecSolutions_djangoserver-space/dealership-package/get-dealership"
        dealer = get_dealer_by_id(url,dealer_id)       
        context["dealer"] = dealer

        url = "https://eu-de.functions.appdomain.cloud/api/v1/web/OpentecSolutions_djangoserver-space/dealership-package/get-reviews"
        # Get reviews from the URL
        reviews = get_dealer_reviews_from_cf(url, dealerId=dealer_id)
        context["review_list"] = reviews
        context["dealerId"] = dealer_id
        return render(request, 'djangoapp/dealer_details.html', context)
# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def add_review(request, dealer_id):
    # Check if user is authenticated first
    context = {}
    print(f"add_review: user authenticated: {request.user.is_authenticated}")
    if request.user.is_authenticated:
        if request.method == "GET":
            # Get dealer object via id
            url = "https://eu-de.functions.appdomain.cloud/api/v1/web/OpentecSolutions_djangoserver-space/dealership-package/get-dealership"
            dealer = get_dealer_by_id(url,dealer_id)
            # Get cars
            cars = CarModel.objects.all()

            context["cars"] = cars
            context["dealer"] = dealer
            return render(request, 'djangoapp/add_review.html', context)

        if request.method == "POST":
            # POST reviews
            form = request.POST
            review = dict()
            review["name"] = f"{request.user.first_name} {request.user.last_name}"
            review["dealership"] = dealer_id
            review["time"] = datetime.utcnow().isoformat()
            review["review"] = form["content"]
            review["purchase"] = False
            if form.get("purchasecheck") == 'on':
                review["purchase"] = True
                review["purchase_date"] = form.get("purchasedate")
            else:
                review["purchase_date"] = None

            car = CarModel.objects.get(pk=form["car"])
            review["car_make"] = car.car_make.name
            review["car_model"] = car.name
            review["car_year"] = car.year

            url = "https://eu-de.functions.appdomain.cloud/api/v1/web/OpentecSolutions_djangoserver-space/dealership-package/post-review"
            json_payload = {"review": review}  # Create a JSON payload that contains the review data

            print(json.dumps(json_payload, indent=2))
            # Performing a POST request with the review
            result = post_request(url, json_payload, dealerId=dealer_id)
            print(f"Status Code after POST: {result.status_code}")

            print("add_review: end")
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)

    else:
        context["message"] = "Please login first to create a review"
        return render(request, 'djangoapp/add_review.html', context)
