import fitz
from tqdm import tqdm
import re
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

pdf2000 = fitz.open('data/pdfs/U1999-2000.pdf')

lines = []
columns = []
texts = []
rounded_lines = []
rounded_columns = []
pages = []

for page_num, page in tqdm(enumerate(pdf2000)):
    soup = BeautifulSoup(page.get_text("html"), "html.parser")
    for p in soup.find_all("p"):
        line = re.findall(r'top:(\d+.\d+)pt', p['style'])[0]
        column = re.findall(r'left:(\d+.\d+)pt', p['style'])[0]
        text = p.getText()
        lines.append(line)
        columns.append(column)
        texts.append(text)
        rounded_lines.append(round(float(line) / 5))
        rounded_columns.append(round(float(column) / 5))
        pages.append(page_num)

raw_data = pd.DataFrame({'text': texts, 
                         'line': lines, 
                         'column': columns, 
                         'rline': rounded_lines, 
                         'rcolumn': rounded_columns, 
                         'page': pages})

raw_data.to_csv('data/raw/U1999-2000.csv')

alphabetical = raw_data[raw_data.page >= 156]
alphabetical.reset_index(inplace=True, drop=True)

pivoted = alphabetical.pivot(index=["page", "rline"], columns='rcolumn', values='text')
cleaned = pivoted[pivoted[17].notna()]
cleaned.reset_index(drop=True, inplace=True)

new_header = cleaned.iloc[0] #grab the first row for the header
cleaned = cleaned[1:] #take the data less the header row
cleaned.columns = new_header #set the header row as the df header

cleaned.to_csv('data/raw/U1999-2000_pivoted.csv', index=False)
cleaned = pd.read_csv('data/raw/U1999-2000_pivoted.csv')

cleaned = cleaned[(pd.notnull(cleaned['Rank']) | (pd.notnull(cleaned['Location'])))]
cleaned.reset_index(drop=True, inplace=True)

#data in PDF entered as "990" instead of 1990
cleaned.loc[1883, 'Start'] = 1990

cleaned.drop(['Unnamed: 1', 'Unnamed: 9', 'Unnamed: 10'], axis=1, inplace=True)

cleaned['graduation_year'] = [re.search("(\d\d)* *(.+)", 
                                        str(x)).group(1) if pd.notnull(x) else x for x in cleaned["Unnamed: 6"]]

cleaned['school_year'] = [re.search("(\d\d)* *(.+)", 
                                    str(x)).group(2) if pd.notnull(x) else x for x in cleaned["Unnamed: 6"]]

cleaned['school_year'] = np.where(cleaned["school_year"].isnull(), 
                                  cleaned["Unnamed: 7"], 
                                  cleaned["school_year"])

cleaned['start_year'] = [re.search("\d*$", 
                                   str(x)).group(0) if pd.notnull(x) else x for x in cleaned["school_year"]]

cleaned['start_year'] = cleaned['start_year'].replace('', np.nan)

cleaned['start_year'] = np.where(cleaned["start_year"].isnull(), 
                                 cleaned["Start"], 
                                 cleaned["start_year"])

cleaned['school'] = [re.search("(\D*) *(\d*)$", 
                               str(x)).group(1).strip() if pd.notnull(x) else x for x in cleaned["school_year"]]

final = cleaned[['Name', 'Rank', 'Location', 'Area', 'Degree', 'graduation_year', 'school', 'start_year']]
final.columns = ['name', 'rank', 'location', 'area', 'degree', 'graduation_year', 'school', 'start_year']

final.to_csv('./data/cleaned/U1999-2000.csv', index=False)
