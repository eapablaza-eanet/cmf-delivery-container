from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True
API_VERSION = '/v1'

MONGO_URI = 'mongodb://cmf-db-delivery:7hajzUGtcfBDUln2zS8zBbgEjNd5zQyE7dKCHlTvWfgiGYZhj9ZJPJ6KnqsBpxV5YfSS2uZMr22EACDbVAUkaw==@cmf-db-delivery.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@cmf-db-delivery@'
TIME_ZONE = 'Chile/Continental'
GOOGLEMAPS_APIKEY = 'AIzaSyD6WjLtmIQ8sf0hqhyArhcORh_e_JWF4Zw'


STATICFILES_DIRS = (str(BASE_DIR.joinpath('static')),)
STATIC_URL = 'static/'

MAX_MIN_ESPERA_PATENTE = 60