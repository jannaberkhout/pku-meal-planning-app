from curl_cffi import requests
import time

list_url = "https://www.voedingscentrum.nl/api/recipes/search?query=*&containsProduct=Vegetarisch&orderByField=2"

payload = {}
headers = {
  'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Referer': 'https://www.voedingscentrum.nl/',
  'X-Requested-With': 'XMLHttpRequest',
  'Connection': 'keep-alive',
  'Cookie': 'ISIS35.NET.PROFILER=VFo9w4e03AEkAAAANGQ5NWM0NGEtZDJiZS00YTAwLTg3MzctMGY0YzZkMWY5ZmE4pgKuYjnVzvq-EqtYtjXUtAiH0KA1; ASP.NET_SessionId=mxn25tkehlrxhz4ougvbarxc; resolution=1920; _ga_SDMC4XN2KQ=GS2.1.s1770992811$o1$g1$t1770993260$j60$l0$h0; _ga=GA1.1.691117388.1770992811; vcRecipeFilters={"searchterm":null,"latestClickedResult":null,"activeFilters":[{"type":"containsProduct","value":"Vegetarisch"}],"filterGroupToggleStatus":[],"orderBy":2}; vcSWA=006d299f-09ab-4cec-b926-1e6dd60b14b7; cc_Cookies=always',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'If-None-Match': '0',
  'TE': 'trailers',
  'Content-Type': 'text/html'
}
print("Get meta data")
list_response = requests.request("GET", list_url, headers=headers, data=payload)

data = list_response.json()

results = data.get('results', None)
if not results:
    raise Exception("No results")

# base_url = "https://www.voedingscentrum.nl/recepten/gezond-recept/"
dir = 'recipes/'
for recipe in results:
    key = recipe.get('key')
    detail_url = f"https://www.voedingscentrum.nl/recepten/gezond-recept/{key}.aspx"
    print(f"GET {detail_url}")
    detail_response = requests.request("GET", detail_url, headers=headers, impersonate="chrome101")
    html = detail_response.text
    with open(dir + key + '.html', 'w') as f:
        f.write(html)
    time.sleep(3)
