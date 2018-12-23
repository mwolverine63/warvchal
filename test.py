import fetch_data
import json

## Import my config
if __name__ == "__main__":
    with open("api_config.json",'r') as f:
        data = json.load(f)
        key = data["auth"]

    #Set the request address
    base_url = 'https://api.royaleapi.com'
    #Add my dev key
    headers = {
        'auth': key
        }

    ## Create the request class
    request = fetch_data.ApiRequest(base_url,headers)

    url = '/player/{}/battles'.format('Y8YJPG8')
    data = request.get_data(url)
    for battle in data:
        print(battle['type'])
    #print(json.dumps(data,sort_keys=True,indent=4, separators=(',', ': ')))