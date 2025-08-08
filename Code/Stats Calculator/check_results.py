# -*- coding: utf-8 -*-
"""
Created on Wed Jul 26 19:27:07 2023
Updated on Mon Aug 7 to work within the Report folder in Autopsy
Updated on Fri Aug 25 to work with reports on individual searches
Updated on Thu Aug 31 with some refactoring and UI updates
Updated on Fri Sept 1 - fixed some path problems
Updated on Tue Sep 5 to use a folder as input and one summary file for all keyword searches
Updated on Wed Sep 6 to include rel/nonrel files and input as either directory or file
+ options to ignore slack files and ignore unallocated
Updated on Fri Sep 8 with some minor fixes
Updated on Wed Sep 20 to include F0.5, F2 and F3 scores in output
"""
import json
import csv
import os
import sys
import argparse
from itertools import zip_longest
from datetime import datetime
from sklearn.metrics import fbeta_score, precision_score, recall_score

def main():
    parser = argparse.ArgumentParser(
                    prog='check_results',
                    description='Takes keyword hits output and an annotation file and computes stats')

    parser.add_argument('-i', '--input', help='path to single file or directory containing JSON files',nargs='?', action='store', dest='searchesfolder')
    parser.add_argument('-a', '--annotation', help='path to annotation file', action='store', dest='annotation_file_path')
    parser.add_argument('-o', '--output', help='path to output folder', action='store', dest='output_folder_path')
    parser.add_argument('--ignoreslack', help='Ignore all slack files', action='store_true', dest='ignore_slack')
    parser.add_argument('--ignoreunalloc', help='Ignore all unallocated files', action='store_true', dest='ignore_unalloc')

    args = parser.parse_args()

    if args.annotation_file_path and not os.path.exists(args.annotation_file_path):
        print("Annotation file does not exist")
        sys.exit(-1)

    if args.output_folder_path and not os.path.exists(args.output_folder_path):
        print("Output folder does not exist")
        sys.exit(-1)

    if args.searchesfolder:
        if os.path.isdir(args.searchesfolder):
            json_files = [f for f in os.listdir(args.searchesfolder) if f.endswith('.json')]
        
            if not json_files:
                print("No JSON files found in the specified folder.")
                sys.exit(0)
            
        elif os.path.isfile(args.searchesfolder) and args.searchesfolder.endswith('.json'):
            json_files = [args.searchesfolder]
            print(json_files)

        else:
            print('panic')
            sys.exit()


        # Create a list to store metrics for each search query
        metrics = []

        for jsonitem in json_files:
           
            if os.path.isdir(args.searchesfolder):
                keyword_hit_export_path = os.path.join(args.searchesfolder, jsonitem)
            else:
                keyword_hit_export_path = jsonitem
                
            analysisfilename = os.path.basename(jsonitem).replace("report-", "").replace(".json", "-")
            output_folder_name = 'analysis-' + analysisfilename + datetime.now().isoformat().replace(':', "-")
            full_output_folder = os.path.join(args.output_folder_path, output_folder_name) if args.output_folder_path else None

            print('Creating folders: {}'.format(full_output_folder))

            res = os.makedirs(full_output_folder, exist_ok=True)
            print(res)

            if args.annotation_file_path:
                summary_file = os.path.basename(jsonitem).replace("report-", "summary-").replace(".json", ".txt")
                summary_file_path = os.path.join(full_output_folder, summary_file)
            else:
                summary_file_path = None

            print('Summary file: {}'.format(summary_file_path))
            
            metricsperjson = json_results(keyword_hit_export_path, args.annotation_file_path, full_output_folder, args.ignore_slack, args.ignore_unalloc)
            metrics.append(metricsperjson)

        # Generate a summary CSV file
        generate_summary_csv(metrics, args.output_folder_path)

def json_results(jsonitem, annotation_file, output_folder, ignore_slack, ignore_unalloc):
    print('ignore_slack = {}'.format(ignore_slack))
    with open(annotation_file, 'r', encoding='utf-8') as file:
        annotation_data = csv.reader(file)
        annotation_dict = {}
        for row in annotation_data:
            if len(row) >= 2:
                fpath = row[0]
                rel = row[1]
                if ignore_slack is True and fpath.endswith('-slack'):
                    pass
                elif ignore_unalloc is True and '/$Unalloc' in fpath:
                    pass
                else:
                    annotation_dict[fpath] = rel

    print(jsonitem)
    with open(jsonitem, 'r') as file:
       json_data =  json.loads(file.read())

    true_positives = set()
    false_positives = set()
    false_negatives = set()
    true_negatives = set()
    processed_files = set()

    relfiles = []
    nonrelfiles = []

    for file_path in annotation_dict:
        if ignore_slack is True and file_path.endswith('-slack'):
            pass
        elif ignore_unalloc is True and '/$Unalloc' in file_path:
            pass
        else:
            if annotation_dict[file_path] == 'r':
                relfiles.append(file_path)
            else:
                nonrelfiles.append(file_path)

    for item in json_data["keyword_hits"]:
        match_path = item.get('match_path')

        if match_path in annotation_dict and match_path not in processed_files:
                processed_files.add(match_path)

                if annotation_dict[match_path] == 'r':
                    true_positives.add(match_path)
                else:
                    false_positives.add(match_path)

    for file_path in annotation_dict:
        if file_path not in processed_files:
            processed_files.add(file_path)

            if annotation_dict[file_path] == 'r':
                false_negatives.add(file_path)
            else:
                true_negatives.add(file_path)

    TP = len(true_positives)
    FP = len(false_positives)
    TN = len(true_negatives)
    FN = len(false_negatives)

    recall = TP / (TP + FN)
    precision = TP / (TP + FP)
   # precision1 = precision_score(y_true=[1]*true_positives + [0]*true_negatives + [0]*false_positives + [0]*false_negatives, y_pred=[1]*true_positives + [0]*true_negatives + [1]*false_positives + [0]*false_negatives)
   # print(precision, precision1)
    #fb score = (1 + b^2) * ((precision * recall) / (b^2 * precision + recall))
    f1 = 2 * ((precision * recall) / (precision + recall))
    f05 = 1.25 * ((precision * recall) / (0.25 * precision + recall))
    f2 = 5 * ((precision * recall) / (4 * precision + recall))
    f3 = 10 * ((precision * recall) / (9 * precision + recall))

    # Write the TP, FP, TN, FN files
    outputfiles(output_folder, 'true_positives.txt', true_positives)
    outputfiles(output_folder, 'false_positives.txt', false_positives)
    outputfiles(output_folder, 'false_negatives.txt', false_negatives)
    outputfiles(output_folder, 'true_negatives.txt', true_negatives)
    


    return {'Searches': os.path.basename(jsonitem).replace("report-", "").replace(".json", ""),
            'Relevant':len(relfiles), 'Non-relevant':len(nonrelfiles),'TP': TP, 'FP': FP, 'TN': TN, 'FN': FN, 'R': recall, 'P': precision,  'F1': f1, 'F05': f05, 'F2': f2, 'F3': f3}

def generate_summary_csv(metrics, output_folder_path):
    if not metrics:
        return

    summary_file_path = os.path.join(output_folder_path, 'summary_results.csv')
    with open(summary_file_path, 'w', newline='') as csv_file:
        fieldnames = ['Searches', 'Relevant', 'Non-relevant','TP', 'FP', 'TN', 'FN', 'R', 'P', 'F1', 'F05', 'F2', 'F3']
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(metrics)

def outputfiles(output_folder, filename, data):
    output_file = os.path.join(output_folder, filename)
    f = open(output_file, 'w')
    for each in data:
      f.write(each + '\n')
    f.close()


main()
