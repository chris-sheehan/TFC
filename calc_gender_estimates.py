import os
import numpy as np
import pandas as pd

PROJECT_DIR = '/Users/csheehan/Documents/projects/tfc'
DATA_DIR = 'data/names/'
DATA_PATH = os.path.join(PROJECT_DIR, DATA_DIR)
NAMES_FILE = os.path.join(DATA_PATH, 'us-living-estimate-names-by-sex.csv')

def binomial_confidence(n, p, size = 10000):
	np.random.binomial(n, p, size).sum()/float(size)

def confidence_interval(name, pick, mean):
	global pvt
	Z = 1.96
	T = int(pvt.loc[name][pick])
	F = int(int(T/mean) - T)
	std = np.append(np.ones(T), np.zeros(F)).std()
	ci = Z * std/np.sqrt(T+F)
	return ci

df = pd.read_csv(NAMES_FILE)
population = df['count'].sum()
pvt = df.pivot(index = 'name', columns = 'sex', values = 'count').fillna(0)
ratios = pvt.div(pvt.sum(axis=1), axis=0)

ratios['sex'] = ratios.apply(lambda row: 'F' if row.F > row.M else 'M', axis =1)
ratios['freq'] = ratios.apply(lambda row: row[row.sex], axis = 1)
ratios['ci'] = ratios.apply(lambda row: confidence_interval(row.name, row.sex, row.freq), axis = 1)
ratios['score'] = ratios.freq - ratios.ci

ratios.drop(['M', 'F'], axis = 1, inplace = True)
save_as = os.path.join(PROJECT_DIR, DATA_DIR, 'sex-estimates-by-name.csv')
ratios.to_csv(save_as, index_label = 'name')
