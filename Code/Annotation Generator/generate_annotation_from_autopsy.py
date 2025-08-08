# 
# 2023-08-xx Initial version
# 2023-09-01 Now removes first part of path from both outputs to remove image name i.e. starts with /volxxx
# 

import argparse
import os
import sys
import csv

def main():
    parser = argparse.ArgumentParser(
                    prog='generate_annotation_from_autopsy',
                    description='Takes file list output from Autopsy and exported bookmarks and generates an annotation file flagging relevant and non-relevant')

    parser.add_argument('-f' '--fullfilelist', help='path to full file list CSV file', action='store', dest='full_file_list_path')       
    parser.add_argument('-b', '--bookmarks',help='path to bookmark export csv file', action='store', dest='bookmarks_path')   
    parser.add_argument('-o', '--output',help='path to output annotation file', action='store', dest='output_file_path')
    parser.add_argument('--force',help='overwrite existing file', action='store_true', dest='force')

    args = parser.parse_args()

    print(args.full_file_list_path)

    if not os.path.exists(args.full_file_list_path):
        print("Full file listing does not exist")
        sys.exit(-1)

    if not os.path.exists(args.bookmarks_path):
        print("Bookmarks file does not exist")
        sys.exit(-1)

    if args.force != True:
        if  os.path.exists(args.output_file_path):
            print("Output file already exists, specify another filename")
            sys.exit(-1)

    bookmark_file = open(args.bookmarks_path, 'r')
    bookmarked_file_list = []
    bookmark_file.readline()
    for each in bookmark_file:
        filename = each.split(',')[1] # from bookmarks/tags the file path is second column
        bookmarked_file_list.append(remove_image_name_from_path(filename))
    bookmark_file.close()

    #print(bookmarked_file_list)
    print("Read {} bookmarks".format(len(bookmarked_file_list)))

    out_annot_file = open(args.output_file_path, 'w')

    print("Reading full file list...")
    no_matched = 0
    file_list_file = open(args.full_file_list_path, 'r')
    for each in file_list_file:
        try:
            csv_reader = csv.reader(file_list_file, delimiter=',')
            for row in csv_reader:
                if len(row) > 0:
                    filename = row[12]
                    filename = remove_image_name_from_path(filename) # we dont want to include the iamge name
                    if filename in bookmarked_file_list:
                        no_matched = no_matched + 1
                        annot = 'r'
                        #print(filename + " - found")
                    else:
                        annot = 'nr'
                        #print(filename + " - not found")
                    out_annot_file.write("{},{}\n".format(filename, annot))
        except IndexError:
            print('Index Error with {}'.format(row))
            quit()
            
    print("Full file list read")
    print("Matched files identified: {}".format(no_matched))

    out_annot_file.close()
    print('Completed')


def remove_image_name_from_path(filename):
    path_parts = filename.strip('\"').lstrip('/').split('/')
    path_with_no_image_name = '/' + '/'.join(path_parts[1:])
    return path_with_no_image_name

main()