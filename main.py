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
			validList.append([zCode, addr+", "+city+", CA, "+zCode, url, codes.query_postal_code('94010', zCode), brandId, "pfizer" not in vaccTypes])

	def sortFunction(e):
		return e[3]

	time = str(datetime.now().strftime("%H:%M:%S"))
	if len(validList) > 0:
		print("\n["+time+"] Found "+str(len(validList))+" appointments:")

		collate = []
		for appt in validList:
			inList = False
			fIdx = 0
			for idx in range(0, len(collate)):
				if collate[idx][0] == appt[4]:
					inList = True
					fIdx = idx;
					break

			if appt[5]:
				unknownType = "*"
			else:
				unknownType = ""

			if not inList:
				collate.append([appt[4], [unknownType+appt[0]]])
			else:
				collate[fIdx][1].append(unknownType+appt[0])

		for idx in range(0, len(collate)):
			vals = collate[idx][1]
			for j in range(0, len(vals)):
				if collate[idx][1][j][0] == "*":
					trueVal = collate[idx][1][j][1:]
				else:
					trueVal = collate[idx][1][j]

				collate[idx][1][j] += "@"+str(round(codes.query_postal_code('94010', trueVal)))
			
			def fn(e):
				return float(e.split("@")[1])
			
			collate[idx][1].sort(key=fn)

		for l in collate:
			print(l[0]+" ("+str(len(l[1]))+"): "+"mi, ".join(l[1])+"mi")
		
		#print("\n\n")
		# validList.sort(key=sortFunction, reverse=True)
		# for appt in validList:
		# 	print("Addr: "+appt[1]+"\nURL: "+appt[2]+"\nDist: "+str(appt[3])+"\n---------------------------")
	else:
		print("["+time+"] No appts found in "+str(len(vaccList))+" places")


while True:
	vaccineCheck()
	time.sleep(10)