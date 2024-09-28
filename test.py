import requests

request = "https://services.ecourts.gov.in"

response = requests.get(request)

print(response.status_code)
print(response)
