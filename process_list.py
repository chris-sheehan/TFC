import os
import numpy as np
import pandas as pd
pd.set_option('display.width', 500)

from fuzzywuzzy import fuzz
from itertools import combinations

PROJECT_DIR = '/Users/csheehan/Documents/projects/tfc'
DATA_DIR = 'data'
DATA_PATH = os.path.join(PROJECT_DIR, DATA_DIR)
NGP_FILE = os.path.join(DATA_PATH, 'lists', 'NGP_Rodman_All.txt')
TFC_FILE = os.path.join(DATA_PATH, 'lists', 'TFC_Central.tsv')

SEX_FILE = os.path.join(DATA_PATH, 'names', 'sex-estimates-by-name.csv')
sex_ratios = pd.read_csv(SEX_FILE, index_col = 'name')
MIN_CONFIDENCE_SEX_ASSIGNMENT = .99

BASIC_COLUMNS = ['contact_id', 'first_name', 'last_name', 'primary_address_1', 'primary_city', 'primary_state', 'primary_zip', 'primary_email_address', 'primary_phone_number', 'is_donor']
TFC_NGP_MAPPING = dict(
	source = 'source',
	id = 'contact_id',
	name = 'mail_name',
	street = 'primary_address_1',
	city = 'primary_city',
	state = 'primary_state',
	zipcode = 'primary_zip',
	)

def load_and_prep_list(filepath, index_col = None):
	df = pd.read_table(filepath)
	if index_col:
		df.set_index(index_col, inplace = True)
	for col in df.columns:
		df.rename(columns = {col : col.replace(' ', '_').lower()}, inplace = True)	
	return df

def estimate_sex_from_first_name(firstname):
	global sex_ratios
	sex = 'U'
	try:
		row = sex_ratios.loc[firstname]
		if row.score > MIN_CONFIDENCE_SEX_ASSIGNMENT:
			sex = row.sex
		else:
			# print fn, row.score
			pass
	except KeyError:
		pass
	return sex

def estimate_sex_from_full_name(fullname):
	split_name = fullname.split()[:-1]
	sex = 'U'
	for name_piece in split_name:
		sex = estimate_sex_from_first_name(name_piece)
		if sex != 'U':
			return sex
	return sex



# NGP
ngp = load_and_prep_list(NGP_FILE)
ngp['is_donor'] = ngp.total_contribution_amount.notnull()

ngp_first_names = ngp.dropna(subset= ['first_name']).first_name.unique()
ngp_first_name_assignments = {fn : estimate_sex_from_first_name(fn) for fn in ngp_first_names}
ngp['sex'] = ngp.first_name.apply(lambda fn: ngp_first_name_assignments.get(fn, 'U'))
ngp['db_source'] = 'ngp'
ngp['in_district'] = False
ngp['non_district_VA'] = False
ngp['non_VA'] = False

# ngp.in_district = ???
## non-district VA cannot be run until sound methodology for in-district is determined!!
va_cities = ngp.loc[(ngp.primary_state == 'VA'),].groupby('primary_city').contact_id.count()
va_cities.sort_values(ascending = False, inplace = True)
non_district_VA_cities = [
'Arlington',
'Alexandria',
'Charlottesville',
'Midlothian',
'Falls Church',
'Ashland',
'Virginia Beach',
'Fairfax',
'North Chesterfield',
'Vienna'
]
# ngp.non_district_VA = ngp.apply(lambda row: ~row.in_district and row.primary_state == "VA", axis = 1)
# ngp.non_district_VA = ngp.apply(lambda row: (row.primary_city in non_district_VA_cities)) and (row.primary_state == "VA"), axis = 1)
ngp.non_district_VA = ngp.primary_city.isin(non_district_VA_cities) & (row.primary_state == "VA")
ngp.non_VA = ngp.primary_state.apply(lambda x: isinstance(x, str) and (x != 'VA'))


#### check dupes by exact matches (email, address)
ngp['full_address'] = ngp.apply(lambda row: '%s %s' % (row.fillna('').primary_address_1, row.fillna('').primary_city), axis = 1)
dupes = ngp[(ngp.primary_address_1.notnull()) & (ngp.primary_city.notnull())].groupby('full_address').contact_id.count()
dupes.sort_values(ascending = False, inplace = True)
dupe_addresses = dupes[dupes > 1].index.tolist()

ngp['potential_dupe'] = False
ngp['dupe_index'] = None
all_match_candidates = list()
for ii in xrange(len(dupe_addresses)):
	print ii,
	address = dupe_addresses[ii]
	combos = combinations(ngp.loc[ngp.full_address == address].index, 2)
	match_candidates = list()
	for ix1, ix2 in combos:
		name1 = ngp.loc[ix1, 'mail_name']
		name2 = ngp.loc[ix2, 'mail_name']
		score = fuzz.WRatio(name1, name2)
		if score > 90:
			match_candidates.append((ix1, ix2))
	for jx1, jx2 in match_candidates:
		ngp.loc[[jx1, jx2], 'potential_dupe'] = True
		ngp.loc[[jx1, jx2], 'dupe_index'] = ('%s_%s' % (jx1, jx2))
	all_match_candidates.extend(match_candidates)
#### check dupes by exact matches (email, address)



# manually found one dupe (by email count)
dupe_ids = ['VTFMGKP0981']
ngp = ngp[ngp.contact_id.isin(dupe_ids) == False]



###################
# TFC

tfc = load_and_prep_list(TFC_FILE)
tfc['sex'] = 'U'
tfc.loc[tfc.source_id == 1, 'sex'] = tfc.loc[tfc.source_id == 1, 'name'].apply(lambda fullname: estimate_sex_from_full_name(fullname))
tfc['db_source'] = 'tfc'
# tfc_full_names = {ix :  row['name'] for ix, row in tfc.loc[(tfc.source_id == 1), ['name']].iterrows()}



contacts = pd.concat([tfc.rename(columns = TFC_NGP_MAPPING), ngp])


# Names from source_id == 5 (OpenSecrets) include a lot of businesses, \
# and individual names are formatted as LASTNAME, FIRSTNAME
# Names from source_id == 1 (VA Dept of Elections) are fmtd as Firstname [M[iddle]] Lastname

