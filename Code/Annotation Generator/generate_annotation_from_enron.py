# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 20:14:56 2023

"""

''' the input looks for example like this:
    1,1,1,
    2,2,1
    3,10,1
 we strip the last one and then we only check the pairs of each row
 '''

import os
import shutil

def checkforcategories(getcats):
    legalcats = [(2, 8), (3, 10)]
    
    #this needs to only look at pairs of numbers so a step of 2
    for i in range(0, len(getcats) - 1,2):
        currentpair = (getcats[i], getcats[i + 1])
        #print(current_pair)
        if currentpair in legalcats:
            return True

    return False





def findfiles(rootf):
    legalfiles = []
    for foldernumber in range(1, 9): #iterate through all the folders
        folderpath = os.path.join(rootf, str(foldernumber))

        for filen in os.listdir(folderpath):
            if filen.endswith(".cats"):
                cats_filepath = os.path.join(folderpath, filen)
                
                with open(cats_filepath, 'r') as f:
                    lines = f.readlines()

                getcats = []
                for line in lines:
                    categories_str = line.strip()
                    #cast the numbers as integers and only keep the first two of each row
                    categories = [int(cat) for cat in categories_str.split(",")[:2]]
                    getcats.extend(categories)
                    

                # cehcking for 2.8 and 3.10
                if checkforcategories(getcats):
                    legalfiles.append(cats_filepath)
                
    
    return legalfiles

if __name__ == "__main__":
    rootf = "OGdataset/"
    legalfiles = findfiles(rootf)
    
    rrootf=os.path.abspath(os.path.join(rootf, os.pardir))
    relevant = os.path.join(rrootf, "relevant")
    nonrelevant = os.path.join(rrootf, "nonrelevant")

    if not os.path.exists(relevant):
        os.makedirs(relevant)

    if not os.path.exists(nonrelevant):
        os.makedirs(nonrelevant)

    annf = os.path.join(rrootf, 'annotation.dic')
    annfile = open(annf, "w")
    
    #moving files to relevant and nonrelevant folders
    for foldernumber in range(1, 9):
        folderpath = os.path.join(rootf, str(foldernumber))

        for filen in os.listdir(folderpath):
            if filen.endswith(".txt"):
                filepath = os.path.join(folderpath, filen)

                if filepath.replace(".txt", ".cats") in legalfiles:
                    # Move the txt file to the "relevant" folder
                    shutil.copy(filepath, os.path.join(relevant, filen))
                    #annfile.write(filen + ', r\n')
                else:
                    # Move the txt file to the "nonrelevant" folder
                    shutil.copy(filepath, os.path.join(nonrelevant, filen))
                    #annfile.write(filen + ', nr\n')

    #creating the annotation file from the two new directories
    
    
    for filen in os.listdir(relevant):
        annfile.write(filen + ',r\n')
    for filen in os.listdir(nonrelevant):
                with open(annf, "a") as annfile: 
                    annfile.write(filen + ',nr\n')
           


    
'''   if legalfiles:
        print("Files annotated as legal-related:")
        for filepath in legalfiles:
            print(filepath.replace(rootf, ""))
    else:
        print("No files found.")
    
    print(len(legalfiles)) '''
    
    