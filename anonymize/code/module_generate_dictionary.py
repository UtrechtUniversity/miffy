import pandas as pd
import hashlib


def generate_dictionary():
    # load datasets used for the dictionary
    to_be_hashed1 = pd.read_table('code/Firstnames_NL.lst', header=None)
    to_be_hashed2 = (pd.read_json('datadownload/connections.json').reset_index()[['index']])
    to_be_hashed3 = (pd.read_json('datadownload/searches.json').reset_index()[['search_click']])
    to_be_hashed4 = (pd.read_json('datadownload/profile.json', typ='series')[['email', 'name', 'username']]).T
    to_be_hashed4 = pd.DataFrame(to_be_hashed4)

    to_be_hashed1.columns = ['names']
    to_be_hashed2.columns = ['names']
    to_be_hashed3.columns = ['names']
    to_be_hashed4.columns = ['names']

    to_be_hashed = pd.concat([to_be_hashed1,
                              to_be_hashed2,
                              to_be_hashed3,
                              to_be_hashed4])

    to_be_hashed.drop_duplicates(subset='names',
                                 keep='first',
                                 inplace=True)

    to_be_hashed = to_be_hashed.reset_index(drop=True)

    for num in range(0, to_be_hashed.shape[0]):
        to_be_hashed.loc[num, 'str2hash'] = hashlib.sha1(to_be_hashed.iloc[num]['names'].encode())

    for num in range(0, to_be_hashed.shape[0]):
        to_be_hashed.loc[num, 'hashies'] = to_be_hashed.iloc[num]['str2hash'].hexdigest()

    hashes_dict = dict(zip(to_be_hashed['names'],
                           to_be_hashed['hashies']))

    return hashes_dict
