
import requests
import json
# import related models here
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features,SentimentOptions


# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    print("get_request: GET from {} ".format(url))
    print(kwargs)
    try:
        # Call get method of requests library with URL and parameters
        response = requests.get(url, headers={'Content-Type': 'application/json'},
                                params=kwargs)
    except:
        # If any error occurs
        print("get_request: Network exception occurred")

    status_code = response.status_code
    #print("get_request: With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, json_payload, **kwargs):
    print(f"post_request: POST to {url}")
    try:
        response = requests.post(url, params=kwargs, json=json_payload)
    except:
        print("post_request: error occurred.")

    status_code = response.status_code
    print(f"post_request: status code - {status_code}")

    return response


# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result
        #print(json.dumps(dealers, indent=4))
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer["doc"]
            
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)

    return results

# Function to return a dealer object given it's ID
def get_dealer_by_id(url, dealer_id):
    results = []
    # Call get_request with the dealer_id param   
    json_result = get_request(url, id=dealer_id)

    # Create a CarDealer object from response
    dealer = json_result[0]
    dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                           id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                           short_name=dealer["short_name"],
                           st=dealer["st"], zip=dealer["zip"])
    return dealer_obj

# Function to return dealer object given the state
def get_dealers_by_state(url, state):
    results = []
    # Call get_request with the state param
    json_result = get_request(url, st=state)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result
        # 
        # For each dealer object
        for dealer_doc in dealers:

            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)
    else:
        print ("get_dealer_by_state: no results!")

    return results

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list
def get_dealer_reviews_from_cf(url, dealerId):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url,dealerId=dealerId)
    if json_result:
        reviews = json_result["data"]["docs"]
        #print(json.dumps(reviews, indent=4))
        # For each review object
        for rev in reviews:
            # Create a DealerReview object with values returned from CF
            # Existing data set has records that may not contain:
            #   car_make=None, car_model=None, car_year=None, purchase_date=None, sentiment="neutral")
            review_obj = DealerReview(dealership=rev["dealership"], name=rev["name"],
                                   purchase=rev["purchase"], review=rev["review"],
                                   )
            if "purchase_date" in rev:
                review_obj.purchase_date = rev["purchase_date"]
            if "car_make" in rev:
                review_obj.car_make = rev["car_make"]
            if "car_model" in rev:
                review_obj.car_model = rev["car_model"]
            if "car_year" in rev:
                review_obj.car_year = rev["car_year"]

            review_obj.sentiment = analyze_review_sentiments(review_obj.review)
            #print("Sentiment: "+review_obj.sentiment)
            results.append(review_obj)

    return results


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def analyze_review_sentiments(text):
    url = "https://api.eu-de.natural-language-understanding.watson.cloud.ibm.com/instances/56b74b83-ef3c-4b9e-ba17-55d6173ff614"
    api_key = "Dl5k2v9ymGn1P5ncuzsXdMW98W62F7fOZmLPqhx2N0LF"
    # version='2022-04-07' / version='2021-08-01'
    authenticator = IAMAuthenticator(api_key)
    natural_language_understanding = NaturalLanguageUnderstandingV1(version='2022-04-07',authenticator=authenticator)
    natural_language_understanding.set_service_url(url)
    try:
        response = natural_language_understanding.analyze( text=text ,features=Features(sentiment=SentimentOptions(targets=[text]))).get_result()
        label=json.dumps(response, indent=2)
        # print(json.dumps(response, indent=2))
        label = response['sentiment']['document']['label']
    except:
        print("NLU returned an error - assume NEUTRAL")
        label = "neutral"

    return(label)