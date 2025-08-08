# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 18:05:56 2023

"""
  
import csv
import os
import random
import string
from nltk.corpus import words
english_words = words.words()


#Non relevant file creation
def generate_random_word():
    random_word = random.choice(english_words)
    return random_word

def create_random_word_files(csv_file):
    with open(csv_file, 'r',  encoding='utf-8') as file:
        reader = csv.reader(file)
        relevant = list(reader)[1:]  # Exclude the first row [!] assumes relevant data is in second column, starts in second row

    output_dir = os.path.splitext(csv_file)[0] + '_output' + '/data'
    os.makedirs(output_dir, exist_ok=True)
    
    relevant_files = []
    non_relevant_files = []

    for index, relevant_word in enumerate(relevant, start=1):
        random_word = generate_random_word()  # Generate a random English word
        relevant_output_file = os.path.join(output_dir, f'r{index}.txt')
        non_relevant_output_file = os.path.join(output_dir, f'nr{index}.txt')

        with open(relevant_output_file, 'w', encoding='utf-8') as relevant_file, open(non_relevant_output_file, 'w') as non_relevant_word_file:
            relevant_file.write(relevant_word[1])  #Airport name is second column
            non_relevant_word_file.write(random_word)
            
            # Adding whitespace for non-resident files
            whitespace_size = 1050 # - len(random_word.encode('utf-8')) - 1
            whitespace = ' ' * whitespace_size
            relevant_file.write('\n' + whitespace)
            non_relevant_word_file.write('\n' + whitespace)
         
            
        relevant_files.append((os.path.basename(relevant_output_file), 'r'))
        non_relevant_files.append((os.path.basename(non_relevant_output_file), 'nr'))    

        print(f"Created file {relevant_output_file} with relevant name: {relevant_word[1]}")
        print(f"Created file {non_relevant_output_file} with random word: {random_word}")
        
    output_dir1 = os.path.splitext(csv_file)[0] + '_output'   
    output_file_list = os.path.join(output_dir1, 'annotation.dic')
    with open(output_file_list, 'w', encoding='utf-8') as output_file:
        for file_name, relevance in sorted(relevant_files + non_relevant_files, key=lambda x: x[0]):
            output_file.write(f"{file_name},{relevance}\n")


            
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(current_dir, 'airports.csv')
create_random_word_files(csv_file)