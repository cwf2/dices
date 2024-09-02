#
# Import statements
#

import pandas as pd
import os
import shutil
import time
import argparse

#
# Global values
#

sheets = [
    'Iliad', 
    'Odyssey',
    'Theogony',
    'Works and Days',    
    'Apollonius',
    'Vergil',
    'Ovid',
    'Lucan',
    'Valerius Flaccus',
    'Silius',
    'Thebaid',
    'Achilleid',
    'Dionysiaca',
    'Paraphrase',    
    'Quintus',
    'Orphic Argonautica',
    'Triphiodorus, Sack of Troy',
    'Moschus, Europa',
    'Theocritus, Idylls',
    'Ps.-Moschus, Megara',
    'Colluthus',
    'Musaeus',
    'Ps.-Homer, Batrachomyomachia',
    'Oppian, Cynegetica',
    'Oppian, Halieutica',
    'Homeric Hymns',
    'Callimachean Hymns',
    'Eudocia, St. Cyprian',
    'Eudocia, Homerocentones',
#    'Proclus, Hymns',
#    'Nicander, Theriaca',
#    'Nicander, Alexipharmaca',
#    'Paul the Silentiary, D. Ambonis',
    'Paul t. S., D. Sanctae Sophiae',
    'Claudian, Eutr.',
    'Claudian, Gild.',
    'Claudian, Ol.Prob.',
    'Claudian, Ruf.',
    'Claudian, Stil.',
    'Claudian, 3 Hon.',
    'Claudian, 4 Hon.',
    'Claudian, epith.',
    'Claudian, 6 Hon.',
    'Claudian, Manl.',
    'Claudian, Goth.',
    'Claudian, rapt.',
    'Prudentius, Psychomachia',
]
fields = [
    'seq',
    'work_id',
    'from_book',
    'from_line',
    'to_book',
    'to_line',
    'simple_cluster_type',
    'cluster_id',
    'cluster_part',
    'speaker',
    'speaker_notes',
    'speaker_disguise',
    'addressee',
    'addressee_notes',
    'addressee_disguise',
    'embedded_level',
    'short_speech_type',
    'long_speech_type',
    'misc_notes',
]


#
# Function Definitions
#

def readTable(table, xls_file, dtype=None, cols=None):
    '''Read a table from the Excel file'''
    
    print(f'Reading {table}...', end='')
    df = pd.read_excel(xls_file, table, dtype=dtype)
    if cols is not None:
        df = df[cols]
    print('{} rows'.format(len(df)))

    return df
    

def writeTable(df, filename, dest_dir):
    '''Write tab-separated data out'''
    
    file_out = os.path.join(dest_dir, filename)
    print(f'Writing {file_out}')
    df.to_csv(file_out, sep='\t', index=False)


#
# Parse commandline args
#

parser = argparse.ArgumentParser(description='Convert Excel workbook into tsv files for DICES')
parser.add_argument('xls_file', type=str, help='Excel file to convert')
parser.add_argument('dest_dir', type=str, help='Destination directory')
args = parser.parse_args()


#
# Read Excel File
#

# authors, works, characters

authors = readTable('Authors', args.xls_file)
works = readTable('Works', args.xls_file, dtype={'author':'Int64'})
characters = readTable('Characters', args.xls_file, dtype='str', cols=['name', 'wd', 'manto', 'topostext', 'being', 'number', 'gender', 'disguise','same_as', 'anon', 'notes'])

# speeches

speech_tables = []

for i, sheet in enumerate(sheets):
    df = readTable(sheet, args.xls_file, dtype={
        'from_book':'str', 'from_line':'str',
        'to_book':'str', 'to_line':'str',
        'cluster_id':'Int64',
        'cluster_part':'str',
        'embedded_level':'Int64',})
    filename = 'speeches_{i:02d}_{name}'.format(i=i, name=sheet.replace(' ', '_'))
    speech_tables.append((filename, df))

    # create unique cluster_id by appending work_id
    df['cluster_id'] += df['work_id'] * 1000


#
# Write CSV files
#

# start with clean destination directory
if os.path.exists(args.dest_dir):
    print(f'Clobbering {args.dest_dir}!')
    shutil.rmtree(args.dest_dir)
os.makedirs(args.dest_dir)

# write authors, works, characters
writeTable(authors, 'authors', args.dest_dir)
writeTable(works, 'works', args.dest_dir)
writeTable(characters, 'characters', args.dest_dir)

# write speeches
for filename, df in speech_tables:
    writeTable(df, filename, args.dest_dir)