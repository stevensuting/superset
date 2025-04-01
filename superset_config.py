ENABLE_PROXY_FIX = True

SECRET_KEY = "45rRYX654erTu$R987654erg"

SQLALCHEMY_DATABASE_URI= "postgresql+psycopg2://superset:superset@db:5432/superset"

#SQLALCHEMY_DATABASE_URI = (os.environ.get("SQLALCHEMY_DATABASE_URI"))

FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_cache',
    'CACHE_REDIS_URL': 'redis://redis:6379/0'
}
DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "SupersetMetastoreCache",
    "CACHE_KEY_PREFIX": "superset_results",  # make sure this string is unique to avoid collisions
    "CACHE_DEFAULT_TIMEOUT": 86400,  # 60 seconds * 60 minutes * 24 hours
}            

