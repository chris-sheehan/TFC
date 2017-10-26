import requests
import json
import time

import pandas as pd

URL_CANDIDATES = """http://gismaps.vita.virginia.gov/arcgis/rest/services/Geocoding/VGIN_Composite_Locator/GeocodeServer//findAddressCandidates?SingleLine={encoded_address}&f=json&outSR=%7B%22wkid%22%3A102100%2C%22latestWkid%22%3A3857%7D&outFields=Loc_name%2C%20Score%2C%20Match_addr&callback=dojo.io.script.jsonp_dojoIoScript3._jsonpCallback"""
URL_DISTRICT = """https://services.arcgis.com/khkECTcXLYiCOD1W/arcgis/rest/services/wml_updated_new/FeatureServer/1/query?f=json&where=&returnGeometry=true&spatialRel=esriSpatialRelIntersects&geometry=%7B%22x%22%3A%22{xcoord}%22%2C%22y%22%3A%22{ycoord}%22%2C%22spatialReference%22%3A%7B%22wkid%22%3A102100%2C%22latestWkid%22%3A3857%7D%7D&geometryType=esriGeometryPoint&inSR=102100&outFields=*&outSR=102100"""

# high income = [23229, 23233, 23060]
ZIP_MAPPING = {
	23238 : 'W',
	23229 : 'S',
	23233 : 'W',
	23060 : 'N',
	23294 : 'N',
	23228 : 'E',
	23226 : 'E',
	23230 : 'E',
	23227 : 'E',
}

def build_address(row):
	address = ' '.join([row.primary_address_1, row.primary_address_2, row.primary_address_3, row.primary_city, row.primary_state, row.primary_zip])
	return address

def get_district(address):
	x, y = get_coordinates(address)
	district = 'Not Found'
	if x:
		district = get_district_from_coords(x, y)
	return district

def get_coordinates(address):
	# address = """10734 High Mountain Ct, Glen Allen, VA 23060"""
	url = build_candidates_url(address)
	json_resp = get_json_response(url)
	top_candidate = pick_best_candidate(json_resp)
	x, y = False, False
	if top_candidate:
		x, y = top_candidate.get('location').get('x'), top_candidate.get('location').get('y')
	return x, y

def build_candidates_url(address):
	encoded_address = requests.utils.quote(address)
	url = URL_CANDIDATES.format(encoded_address = encoded_address)
	return url

def get_json_response(url):
	resp = requests.get(url)
	if not resp.ok:
		json_resp = False
	else:
		try:
			json_resp = json.loads(resp.text.replace('dojo.io.script.jsonp_dojoIoScript3._jsonpCallback(', '')[:-2])
		except:
			json_resp = False
	return json_resp

def pick_best_candidate(json_resp):
	candidates = json_resp.get('candidates')
	top_candidate = None
	top_score = 0
	for candidate in candidates:
		if candidate.get('score', 0) >= top_score:
			top_candidate = candidate
			if candidate.get('score', 0) == 100:
				return candidate
	return top_candidate


def get_district_from_coords(x, y):
	url = URL_DISTRICT.format(xcoord = x, ycoord = y)
	resp = requests.get(url)
	json_resp =resp.json()
	try:
		district = json_resp.get('features')[0].get('attributes').get('DistrictNum')
	except (KeyError, IndexError):
		district = None
	return district

def map_zip_region(zipcode):
	try:
		zipcode = int(zipcode[:5])
		region = ZIP_MAPPING.get(zipcode)
	except ValueError:
		region = None
	return region


contacts = pd.read_table('data/lists/NGP_Rodman_Processed.txt')
contacts.fillna('', inplace = True)
contacts['district'] = ''

for ix, row in contacts[contacts.district == ''].iterrows():
	district = 'NA'
	if row.primary_state == 'VA':
		address = build_address(row)
		district = get_district(address)
		time.sleep(1)
	contacts.loc[ix, 'district'] = district
	if (ix % 25) == 0:
		print 'Saving after %s records.' % ix
		contacts.to_csv('NGP_Rodman_Processed_wDistrict.txt', sep = '\t', index = False)

contacts.to_csv('NGP_Rodman_Processed_wDistrict.txt', sep = '\t', index = False)

contacts['region'] = None
contacts.loc[(contacts.primary_zip.notnull()) & (contacts.district == 73), 'region'] = contacts.loc[(contacts.primary_zip.notnull()) & (contacts.district == 73), 'primary_zip'].apply(lambda z:  map_zip_region(z))
# df.loc[(df.primary_zip.notnull()) & (df.district == '73'), 'region'] = df.loc[(df.primary_zip.notnull()) & (df.district == '73'), 'primary_zip'].apply(lambda z:  map_zip_region(z))
