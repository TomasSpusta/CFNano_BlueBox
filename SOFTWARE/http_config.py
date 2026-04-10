import aiohttp


REQUEST_TIMEOUT = aiohttp.ClientTimeout(
    total=20,
    connect=5,
    sock_read=10,
)

CONNECTIVITY_TIMEOUT = aiohttp.ClientTimeout(
    total=5,
    connect=2,
    sock_read=3,
)
