# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 18:36:14 2023
Updated on Fri Aug 25 to work with reports on individual searches
Updated on Sun 3 Sep to include plots for precision and recall
@author: Katerina
"""


''' Plots '''

import matplotlib.pyplot as plt
import os
import numpy as np

TP_values = []
FP_values = []
TN_values = []
FN_values = []
recall = []
precision = []
namesofsearches = []


noofsearches = len([file for file in os.listdir() if file.endswith('.txt')])
for summary_report in os.listdir():
    if summary_report.endswith('.txt'):
        print(summary_report)
        name_parts = summary_report.split('-')  
        main_name = '-'.join(name_parts[1:]).split('.')[0]
        namesofsearches.append(main_name)
        print(main_name)
        with open(summary_report, 'r', encoding='utf-8') as txt_file:
            lines = txt_file.readlines()

    # Parsing the summary report files to get the numbers of files for eaach category
            TP_values.append(int(lines[3].split(':')[-1].strip()))
    #print(TP_values)
            FP_values.append(int(lines[4].split(':')[-1].strip()))
    #print(FP_values)
            TN_values.append(int(lines[5].split(':')[-1].strip()))
    #print(TN_values)
            FN_values.append(int(lines[6].split(':')[-1].strip()))
    #print(FN_values)
            recall.append(float(lines[8].split('=')[-1].strip()))
            precision.append(float(lines[9].split('=')[-1].strip()))



fig, axes = plt.subplots(2, 2, figsize=(12, 8))
xvalues = list(namesofsearches)
bar_width = 0.5

# Plot TP
axes[0, 0].bar(xvalues, TP_values, width=bar_width)
axes[0, 0].set_title('True Positives (TP)')
axes[0, 0].set_xlabel('Searches')
axes[0, 0].set_ylabel('Number of Files')
axes[0, 0].set_xticklabels(namesofsearches,fontsize= 6, rotation=15, ha='right')

# Plot FP
axes[0, 1].bar(xvalues, FP_values, width=bar_width,  color = 'orange')
axes[0, 1].set_title('False Positives (FP)')
axes[0, 1].set_xlabel('Searches')
axes[0, 1].set_ylabel('Number of Files')
axes[0, 1].set_xticklabels(namesofsearches, fontsize= 6, rotation=15, ha='right')

# Plot TN
axes[1, 0].bar(xvalues, TN_values, width=bar_width,  color = 'tab:gray')
axes[1, 0].set_title('True Negatives (TN)')
axes[1, 0].set_xlabel('Searches')
axes[1, 0].set_ylabel('Number of Files')
axes[1, 0].set_xticklabels(namesofsearches, fontsize= 6, rotation=15, ha='right')

# Plot FN
axes[1, 1].bar(xvalues, FN_values, width=bar_width, color = 'purple')
axes[1, 1].set_title('False Negatives (FN)')
axes[1, 1].set_xlabel('Searches')
axes[1, 1].set_ylabel('Number of Files')
axes[1, 1].set_xticklabels(namesofsearches,  fontsize= 6, rotation=15, ha='right')



plt.subplots_adjust(hspace=0.5)
plt.show()

######
#creating recall and precision plots

fig, ax = plt.subplots()
xvalues = np.arange(len(namesofsearches))
bar_width = 0.35

ax.bar(xvalues - bar_width / 2, recall, width=bar_width, label='Recall', color='tab:blue')
# Plot Precision
ax.bar(xvalues + bar_width / 2, precision, width=bar_width, label='Precision', color='tab:gray', alpha=0.7)

ax.set_title('Recall and Precision')
ax.set_xlabel('Searches')
ax.set_ylabel('Number of Files')
ax.set_xticks(xvalues)
ax.set_xticklabels(namesofsearches, rotation=15, fontsize=7, ha='right')
ax.legend()

plt.tight_layout()
plt.show()


