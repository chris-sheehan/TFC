import os
import numpy as np
import pandas as pd
pd.set_option('display.width', 500)

PROJECT_DIR = '/Users/csheehan/Documents/projects/tfc'
DATA_DIR = 'data'
DATA_PATH = os.path.join(PROJECT_DIR, DATA_DIR)
NGP_FILE = os.path.join(DATA_PATH, 'lists', 'NGP_Rodman_All.txt')
TFC_FILE = os.path.join(DATA_PATH, 'lists', 'TFC_Central.tsv')

SEX_FILE = os.path.join(DATA_PATH, 'names', 'sex-estimates-by-name.csv')
sex_ratios = pd.read_csv(SEX_FILE, index_col = 'name')
MIN_CONFIDENCE_SEX_ASSIGNMENT = .99

BASIC_COLUMNS = ['contact_id', 'first_name', 'last_name', 'primary_address_1', 'primary_city', 'primary_state', 'primary_zip', 'primary_email_address', 'primary_phone_number', 'is_donor']

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




ngp = load_and_prep_list(NGP_FILE)
ngp['is_donor'] = ngp.total_contribution_amount.notnull()

ngp_first_names = ngp.dropna(subset= ['first_name']).first_name.unique()
ngp_first_name_assignments = {fn : estimate_sex_from_first_name(fn) for fn in ngp_first_names}
ngp['sex'] = ngp.first_name.apply(lambda fn: ngp_first_name_assignments.get(fn, 'U'))


tfc = load_and_prep_list(TFC_FILE)
tfc['sex'] = 'U'
tfc.loc[tfc.source_id == 1, 'sex'] = tfc.loc[tfc.source_id == 1, 'name'].apply(lambda fullname: estimate_sex_from_full_name(fullname))
# tfc_full_names = {ix :  row['name'] for ix, row in tfc.loc[(tfc.source_id == 1), ['name']].iterrows()}




# Names from source_id == 5 (OpenSecrets) include a lot of businesses, \
# and individual names are formatted as LASTNAME, FIRSTNAME
# Names from source_id == 1 (VA Dept of Elections) are fmtd as Firstname [M[iddle]] Lastname

