import os

API_VERSION = '/v1'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'flask-insecure-7ppocbnx@w71dcuinn*t^_mzal(t@o01v3fee27g%rg18fc5d@'

# Configure allowed host names that can be served and trusted origins for Azure Container Apps.
ALLOWED_HOSTS = ['.azurecontainerapps.io'] if 'RUNNING_IN_PRODUCTION' in os.environ else []
CSRF_TRUSTED_ORIGINS = ['https://*.azurecontainerapps.io'] if 'RUNNING_IN_PRODUCTION' in os.environ else []
DEBUG = False

# Configure database connection for Azure PostgreSQL Flexible server instance.
# AZURE_POSTGRESQL_HOST is the full URL.
# AZURE_POSTGRESQL_USERNAME is just name without @server-name.

MONGO_URI = 'mongodb://cmf-db-delivery:7hajzUGtcfBDUln2zS8zBbgEjNd5zQyE7dKCHlTvWfgiGYZhj9ZJPJ6KnqsBpxV5YfSS2uZMr22EACDbVAUkaw==@cmf-db-delivery.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@cmf-db-delivery@'
TIME_ZONE = 'Chile/Continental'
GOOGLEMAPS_APIKEY = 'AIzaSyD6WjLtmIQ8sf0hqhyArhcORh_e_JWF4Zw'

MAX_MIN_ESPERA_PATENTE = 60