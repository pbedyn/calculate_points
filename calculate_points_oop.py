# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 22:02:26 2023

@author: pawel
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
from fuzzywuzzy import fuzz
from io import StringIO

class CompetitionPointsCalculator:
    def __init__(self, comp_name, comps):
        self.comp_name = comp_name
        self.comps = comps
        self.match_comp_name()

    def match_comp_name(self):
        def calc_fuzz_ratio(comp_name, comp_in_table):
            return fuzz.ratio(comp_name, comp_in_table)

        self.comps['ratio'] = self.comps['competition'].apply(lambda x: calc_fuzz_ratio(self.comp_name, x))
        max_match = max(self.comps['ratio'])
        self.comp_name = self.comps['competition'][self.comps['ratio'] == max_match].to_list()[0]
        self.url = self.comps['link'][self.comps['competition'] == self.comp_name].to_list()[0]
        self.comp_site = self.comps['site'][self.comps['competition'] == self.comp_name].to_list()[0]
        self.num_pilots = self.comps['max_participants'][self.comps['competition'] == self.comp_name].to_list()[0]

    ###############################################################################
    def scrape_airtribune(self, url):
        """
        Scrapes data from an airtribune website using the url passed as an argument.
        Manually searches for the beginning and end of the json table
        Returns the comp dataframe
        """
        # Make a request to the website and scrape the given comp site
        response = requests.get(url)
    
        # Parse the HTML content of the website
        soup = BeautifulSoup(response.content, 'html.parser')
        all_data = StringIO(str(soup)).read()
    
        # Manually extracts data finding beginning and end of json table
        start_table = all_data.find('"pilots": [')
        end_table = all_data[start_table:].find('}]')
        all_data = all_data[start_table+len('"pilots": [')-1:start_table+end_table+2]
        all_data = all_data.replace('https://', '')
        all_data = all_data.replace('http://', '')
        comp = pd.read_json(all_data, orient='records')
       
        # correct nan in civl_id
        comp['civl_id'] = comp['civl_id'].replace(np.nan, int(99999))
        comp['civl_id'] = pd.to_numeric(comp['civl_id'])
        
        # standardize the status column
        comp['status'] = comp['status'].str.lower()
        return comp
    
    ###############################################################################
    def scrape_civl(self, url):
        """
        Scrape data from a CIVL comp website using the url passed as an argument.
        Note: extract the table element with the class 'participants-item'.
        Returns the comp dataframe
        """
        # function to extract numbers from the Name column
        def extract_numbers(value_in):
            return re.sub("[^\d+]", "", value_in)
       
        # function to extract names from the Name column
        def extract_names(value_in):
            return re.sub("[^a-zA-ZÀ-ÿ.]+$", " ", value_in)[:-1].lower()
       
        # make a request to the website and scrape the given comp site
        response = requests.get(url)
        # parse the HTML content of the website
        soup = BeautifulSoup(response.content, 'html.parser')
        # finds json table using the "participants-item" class
        comp = pd.DataFrame(columns = ['No', 'Name', 'Number', 'Wing', 'Sponsor', 'status'])
       
        tables = soup.find_all('div', {'class': 'participants-item'})
        for table in tables:
            rows = table.find_all('tr')
            data = [[col.text for col in row.find_all('td')] for row in rows]
            data = pd.DataFrame(data, columns = ['No', 'Name', 'Number', 'Wing', 'Sponsor', 'status'])
            data = data.loc[1:,]
            comp = pd.concat([comp, data])
        # extract Number and correct the names (note: names are returned in lower case)
        comp['Number'] = comp['Name'].apply(lambda x: extract_numbers(x))
        comp['Name'] = comp['Name'].apply(lambda x: extract_names(x))
        
        # standardize the status column
        comp['status'] = comp['status'].str.lower()
        return comp
    
    ###############################################################################
    def scrape_ffvl(self, url):
        """
        Scrape data from the FFVL comp website using the url passed as an argument.
        Note: extract the table element with the class 'table-responsive'.
        Returns the comp dataframe
        """
        # function to extract numbers from the Name column
        def extract_numbers(value_in):
            return re.sub("[^\d+]", "", value_in)
       
        # function to extract names from the Name column
        def extract_names(value_in):
            return re.sub("[^a-zA-ZÀ-ÿ.]+$", " ", value_in)[:-8].lower()
       
        # make a request to the website and scrape the given comp site
        response = requests.get(url)
        # parse the HTML content of the website
        soup = BeautifulSoup(response.content, 'html.parser')
        # finds json table using the "participants-item" class
        table = soup.find('div', {'class': 'table-responsive'})
        rows = table.find_all('tr')
        data = [[col.text for col in row.find_all('td')] for row in rows]
        comp = pd.DataFrame(data, columns = ['No', 'Name', 'civl_id', 'Reg', 'status', 'Ranking'])
        comp = comp.loc[1:,]
        # extract Number and correct the names (note: names are returned in lower case)
        comp['Country'] = comp['Name'].str[:3]
        comp['Name'] = comp['civl_id'].apply(lambda x: extract_names(x))
        comp['civl_id'] = comp['civl_id'].apply(lambda x: extract_numbers(x))
        comp['civl_id'] = pd.to_numeric(comp['civl_id'])
        comp['civl_id'] = comp['civl_id'].replace(np.nan, int(99999))
        
        # standardize the status column
        comp['status'] = comp['status'].str.lower()
        return comp
    
    ###############################################################################
    def scrape_pwc(self, url):
        """
        Scrape data from a CIVL comp website using the url passed as an argument.
        Note: extract the table element with the class 'participants-item'.
        Returns the comp dataframe
        """
        # function to extract numbers from the Name column
        def extract_numbers(value_in):
            return re.sub("[^\d+]", "", value_in)
       
        # function to extract names from the Name column
        def extract_names(value_in):
            return re.sub("[^a-zA-ZÀ-ÿ.]+$", " ", value_in)[:-1].lower()
       
        # list of pages to scrape
        url_list = ["?gender=male", "?gender=female"]
        # make a request to the two jsons containing male and femals
        # participants and scrape the given comp site
        comp = pd.DataFrame(columns = ['season_number', 'pilot', 'country', 'country_flag', \
                                       'glider', 'harness', 'sponsor', 'status', \
                                       'status_key', 'is_late', 'qualification_letters'])
        for url_end in url_list:
            url_to_scrape = url + url_end
            response = requests.get(url_to_scrape)
            # parse the HTML content of the website
            data = response.json()
            data= pd.DataFrame(data['subscriptions'])
            comp = pd.concat([comp, data])
           
        # extract Number and correct the names (note: names are returned in lower case)
        comp['pilot'] = comp['pilot'].str.lower()
        comp = comp.rename(columns={'pilot': 'Name'})
        comp['status'] = comp['status'].str.lower()
        return comp

    ###############################################################################
    def calc_comp_points(self, comp):
        # read in the ranking table
        ranking = pd.read_excel("E:\\Flights\\Competitions\\Rankings\\202303.xlsx")
        ranking_columns = ranking.iloc[3,].to_list()
        ranking = ranking.iloc[4:len(ranking) - 2, ]
        ranking.columns = ranking_columns
        del ranking_columns
        ranking['Name'] = ranking['Name'].str.lower()
        ranking['CIVL ID'] = pd.to_numeric(ranking['CIVL ID'])
       
        # merge the comp table with the ranking table
        if self.comp_site == 'Civl' or self.comp_site == 'PWCA':
            merged_comp = pd.merge(left=comp, right=ranking, how='left', left_on='Name', right_on='Name')
            merged_comp = merged_comp.sort_values(by="Points", axis=0, ascending = False)    
        else:
            merged_comp = pd.merge(left=comp, right=ranking, how='left', left_on='civl_id', right_on='CIVL ID')
            merged_comp = merged_comp.sort_values(by="Points", axis=0, ascending = False)  
        # correct nans in the merged_comp table
        merged_comp['Points'] = pd.to_numeric(merged_comp['Points'])
        merged_comp['Points'] = merged_comp['Points'].replace(np.nan, int(0))
        half_pilots = int(self.num_pilots/2)
        points = round((sum(merged_comp["Points"][0:half_pilots]) / \
                 sum(ranking["Points"][0:half_pilots]) * 0.8 + 0.2) * 120, 1)
            
        merged_comp_conf = merged_comp[merged_comp['status'].isin(['confirmed', 'wildcard'])]
        conf_points = round((sum(merged_comp_conf["Points"][0:half_pilots]) / \
                    sum(ranking["Points"][0:half_pilots]) * 0.8 + 0.2) * 120, 1)
        print(half_pilots)
        return points, conf_points
    
    ###############################################################################
    def run(self):
        if self.comp_site == 'Airtribune':
            comp = self.scrape_airtribune(self.url)
        elif self.comp_site == 'Civl':
            comp = self.scrape_civl(self.url)
        elif self.comp_site == 'FFVL':
            comp = self.scrape_ffvl(self.url)
        else:
            comp = self.scrape_pwc(self.url)

        points, conf_points = self.calc_comp_points(comp)
        return points, conf_points

if __name__ == "__main__":
    comp_name = "British Winter Open"
    comps = pd.read_csv("E:\\Flights\Competitions\\Calculations\\2023\\2023 competitions.csv", index_col=None)
    comp_points = CompetitionPointsCalculator(comp_name, comps)
    points, conf_points = comp_points.run()
    print(points, conf_points)