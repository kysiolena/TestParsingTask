"""
This script creates the ProductInfo instances and saves them to the DB with the status 'New'
"""

from load_django import *  # noqa

from parser_app.models import ProductInfo, Status

# In a real situation, there will be an infinite while True loop here, as long as the page request returns a 200 status code
data = {
    "link": "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html",
    "status": Status.NEW,
}

ProductInfo.objects.get_or_create(**data)
