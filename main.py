import os
import requests
import json
import time
import pgeocode
from datetime import datetime

# Settings
citiesFile = "cities.txt"

cwd = os.path.dirname(os.path.realpath(__file__))


with open(os.path.join(cwd, citiesFile), 'r', encoding="utf8", errors="ignore") as file:
	citiesDataRaw = file.read()


cities = []
validZips = []
for line in citiesDataRaw.split("\n"):
	spl = line.split(",")
	cities.append([int(spl[0]), spl[2], spl[3]])
	validZips.append(spl[0])

codes = pgeocode.GeoDistance('US')

def vaccineCheck():
	#print("Getting vaccine list")
	vaccData = ""
	c = 0
	r = requests.get("https://www.vaccinespotter.org/api/v0/states/CA.json", stream=True)
	if r.status_code == 200:
		for chunk in r:
			vaccData += chunk.decode('utf-8')
			c+=1
		r.close()
	else:
		r.close()
	#print("got "+str(c)+" chunks; parsing")
	vaccList = json.loads(vaccData)["features"]

	validList = []
	for v in vaccList:
		p = v["properties"]

		zCode = p["postal_code"]
		addr = p["address"]
		city = p["city"]
		url = p["url"]

		provId = p["provider_location_id"]
		brandId = p["provider_brand_name"]

		vaccTypes = p["appointment_vaccine_types"]


		if p["appointments_available"] == True and ("pfizer" in vaccTypes or "unknown" in vaccTypes) and zCode in validZips:
			validList.append([zCode, addr+", "+city+", CA, "+zCode, url, codes.query_postal_code('94010', zCode)])

	def sortFunction(e):
		return e[3]

	time = str(datetime.now().strftime("%H:%M:%S"))
	if len(validList) > 0:
		print("["+time+"] Found "+str(len(validList))+" appointments:\n\n")
		
		validList.sort(key=sortFunction, reverse=True)
		for appt in validList:
			print("Addr: "+appt[1]+"\nURL: "+appt[2]+"\nDist: "+str(appt[3])+"\n---------------------------")
	else:
		print("["+time+"] No appts found in "+str(len(vaccList))+" places")


while True:
	vaccineCheck()
	time.sleep(10)