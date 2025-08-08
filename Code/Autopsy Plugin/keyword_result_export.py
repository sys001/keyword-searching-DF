#
# Module for Export Keyword Results into Standard Formats
#
# Makes use of SQLite Schema from here https://wiki.sleuthkit.org/index.php?title=SQLite_Database_v3_Schema
#
# Some notes
    # select artifact_type_id from blackboard_artifact_types where type_name LIKE "TSK_KEYWORD_HIT"
        # should be 9
        
        #
        # select * from blackboard_artifacts where artifact_type_id = 9
        #
        # obj_id ()48, 70 = the file id
        # artifact_obj_id (72, 73)
        #
        # select * from blackboard_attribute_types
        # 10 = TSK_KEYWORD
        # 11 = TSK_KEYWORD_REGEXP 
        # 12 = TSK_TSK_KEYWORD_PREVIEW
        # 13 = TSK_KEYWORD_SET
        # 122 = TSK_KEYWORD_SEARCH_TYPE
        #
        # select * from blackboard_attributes where attribute_type_id == 10 
        # artifact_id in hex is 0x8000000000000001, and 0x8000000000000002
        #
        # tsk_fs_info has a obj_id (5,9) field linked to root_inum (2,5)
        # files actually in 4 and 6
        #
        # addr in tsk_vs_parts is the volumen number
        # addr 4 = obj_id 4, addr 6 is obj 8
        #
        # tsk_fils( fs_obj_id) -> tsk_vs_parts(obj_id) but -11???
        #tsk_files obj_id 5,9 ->  tsk_vs_parts obj_id 4,8
        #       



# Splits output into multiple files for each keyword/keyword list 
# Version xxx Added progress bars to UK
# Version 2023-08-31 now exports valid json (list of dicts) 
# Version 2023-09-01 JSON format updatde to include metadata, and keyword hits in subkey 'keyword_hits'
# Version 2023-09-03 volume name prefixed with _vol to match autopsy notation
# 


import os
import re
from java.lang import System
from java.util.logging import Level
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.report import GeneralReportModuleAdapter
from org.sleuthkit.autopsy.report.ReportProgressPanel import ReportStatus
from org.sleuthkit.autopsy.datamodel import KeywordHits
from org.sleuthkit.autopsy.coreutils import Version
#from org.sleuthkit.autopsy.keywordsearch import KeywordSearch

from javax.swing import JPanel
from javax.swing import JCheckBox
from javax.swing import JSlider
from javax.swing import JLabel
from javax.swing import JList
from javax.swing import JScrollPane
from java.awt import GridLayout
from java.awt import GridBagLayout
from java.awt import GridBagConstraints

import codecs
import logging
import json
from datetime import datetime

class KeywordHit(object):
   
    def __init__(self):
        self.aut_artefact_id = ''
        self.aut_obj_id = ''
        
        self.search_type = ""  # keyword, regex
        self.search_term = ""
        self.match_term = ""
        self.match_encoding = ""
        self.hit_type = "" # file, result?
        self.match_path = ""
        self.match_preview = ""    
        self.keyword_list_name = ""

    def toCSV(self):
        out = '"' + self.search_type + '",' + '"' + self.search_term + '","' + self.match_term + '","' + self.match_path + '","' + self.keyword_list_name + '"' 
        # + self.aut_artefact_id + '\t' + self.aut_obj_id + '\t'
        return out

    def toDict(self):
        out_dict = {}
        out_dict['search_type'] = self.search_type
        out_dict['search_term'] = self.search_term
        out_dict['match_term'] = self.match_term
        #out_dict['match_encoding'] = self.match_encoding
        #out_dict['hit_type'] = self.hit_type
        out_dict['match_path'] = self.match_path
        #out_dict['match_preview'] = self.match_preview
        out_dict['keyword_list_name'] = self.keyword_list_name
        return out_dict

    def asdict(self):
        return self.toDict()


class KeywordResultExportReportModule(GeneralReportModuleAdapter):

    moduleName = "Keyword Export Report Module"

    # Test of some GUI stuff
    def getConfigurationPanel(self):
        self.configPanel = KW_ConfigPanel()
        return self.configPanel

    _logger = None
    def log(self, level, msg):
        if _logger == None:
            _logger = Logger.getLogger(self.moduleName)

        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    def getName(self):
        return self.moduleName

    def getDescription(self):
        return "Export Keyword Results"

    def getRelativeFilePath(self):
        return "keyword_results.txt"

    def get_vol_list(self):
        '''Get list of volumes from database as dictionary indexed on obj_id'''
        skCase = Case.getCurrentCase().getSleuthkitCase()

        logging.info('building volume list')

        sql_statement = 'select obj_id, addr from tsk_vs_parts'
        dbquery = skCase.executeQuery(sql_statement)
        resultSet = dbquery.getResultSet()
                
        vols = {}
        
        while resultSet.next():
            logging.debug(resultSet.getString("obj_id"))
            real_obj = int(resultSet.getString("obj_id")) + 1
            logging.debug(real_obj)

            vols[str(real_obj)] = 'vol' + resultSet.getString("addr")

            logging.debug(str(real_obj)  + ' = '  +'vol' + resultSet.getString("addr"))
        
        dbquery.close()        
        return vols   


    def get_file_list(self):
        '''Get list of files from database as dictionary indexed on obj_id'''
        logging.info("Getting file list...")

        skCase = Case.getCurrentCase().getSleuthkitCase()
        sql_statement = 'select obj_id, fs_obj_id, data_source_obj_id, name, parent_path from tsk_files;'
        dbquery = skCase.executeQuery(sql_statement)
        resultSet = dbquery.getResultSet()
        
        vols = self.get_vol_list()
        files = {}
        
        while resultSet.next():
            try:
                #logging.debug('(obj_id) ' + resultSet.getString('obj_id'))
                #logging.debug('(fs_obj_id) ' + resultSet.getString("fs_obj_id"))
                vol_label = vols[resultSet.getString("fs_obj_id")]
                files[resultSet.getString("obj_id")] = '/vol_' + vol_label + resultSet.getString("parent_path") + resultSet.getString("name")
            except Exception as e:
                logging.error(e)
                logging.error('(obj_id) ' + resultSet.getString('obj_id'))
                #logging.error('(fs_obj_id) ' + resultSet.getString("fs_obj_id"))
                logging.error('(name) ' + resultSet.getString("name"))
                

        dbquery.close()        
        return files   


    def get_artefact_to_object_mappings(self):
        '''Builds a dictionary to allow quick conversion of artifact_id to obj_id from blackboard_artifacts in case database'''
        skCase = Case.getCurrentCase().getSleuthkitCase()
        sql_statement = 'select artifact_id, obj_id, data_source_obj_id, artifact_type_id, review_status_id from blackboard_artifacts where artifact_type_id = 9;'
        dbquery = skCase.executeQuery(sql_statement)
        resultSet = dbquery.getResultSet()

        artefact_to_object_mappings = {}
        
        while resultSet.next():
            artefact_to_object_mappings[resultSet.getString("artifact_id")] = resultSet.getString("obj_id")
            
        dbquery.close()        
        return artefact_to_object_mappings        
    
    
    def get_list_of_plain_keyword_hits(self):
        '''Gets a list of the keyword hits from blackboard_attributes in the case database'''

        logging.info('starting to build keyword list')

        skCase = Case.getCurrentCase().getSleuthkitCase()
        sql_statement = 'select artifact_id, artifact_type_id, source, attribute_type_id, value_type, value_text, value_int32 from blackboard_attributes where artifact_type_id = 9'
        dbquery = skCase.executeQuery(sql_statement)
        resultSet = dbquery.getResultSet()
        
        hits = {} # indexed on autopsy artefact_id
        
        logging.info('looping type 10...')

        # First pass just looks at results
        while resultSet.next():
            if resultSet.getString("attribute_type_id") == '10':   # if TSK_KEYWORD

                # Build Keyword Object
                hit = KeywordHit()
                hit.search_type = 'keyword'
                hit.search_term = resultSet.getString("value_text")
                hit.match_term = resultSet.getString("value_text")
                hit.aut_artefact_id = resultSet.getString("artifact_id")

                # add to the list
                hits[resultSet.getString("artifact_id")] = hit
            
        dbquery.close()   

        logging.info('looping type 11...')
        dbquery = skCase.executeQuery(sql_statement)
        resultSet = dbquery.getResultSet() 
        # Second pass updates those that were regular expressions
        while resultSet.next():
            if resultSet.getString("attribute_type_id") == '11':   # if TSK_KEYWORD

                if hits.get(resultSet.getString("artifact_id")) != None:       
                    logging.debug('{} in list'.format(hits.get(resultSet.getString("artifact_id"))))

                    hits[resultSet.getString("artifact_id")].search_type = 'regex'
                    hits[resultSet.getString("artifact_id")].search_term = resultSet.getString("value_text")
                else:
                    logging.error('{} not in list'.format(hits.get(resultSet.getString("artifact_id"))))
        dbquery.close()  


        logging.info('looping type 37...')
        dbquery = skCase.executeQuery(sql_statement)
        resultSet = dbquery.getResultSet() 
        # Second pass updates those that came from a named keyword list
        while resultSet.next():
            if resultSet.getString("attribute_type_id") == '37':   # if TSK_SET_NAME

                if hits.get(resultSet.getString("artifact_id")) != None:       
                    logging.debug('{} in list'.format(hits.get(resultSet.getString("artifact_id"))))

                    hits[resultSet.getString("artifact_id")].keyword_list_name = resultSet.getString("value_text")
                else:
                    logging.error('{} not in list'.format(hits.get(resultSet.getString("artifact_id")))) 
        dbquery.close()  

        # can do more with previews and lists if necessary
        # elif resultSet.getString("attribute_type_id") == '11':   # is TSK_KEYWORD_REGEXP
        #     pass

        # elif resultSet.getString("attribute_type_id") == '12':   # is TSK_TSK_KEYWORD_PREVIEW
        #     pass

        # elif resultSet.getString("attribute_type_id") == '13':   # is TSK_KEYWORD_SET
        #     pass

        # elif resultSet.getString("attribute_type_id") == '37':   # is TSK_SET_NAME
        #     pass

        # elif resultSet.getString("attribute_type_id") == '122':   # is TSK_KEYWORD_SEARCH_TYPE
        #     pass


        # convert to list
        hits_list = []
        for each in hits:
            hits_list.append(hits[each])

        return sorted(hits_list, key=lambda x:x.search_term)

    
    def generate_csv_and_json_reports(self, list_of_hits, reportSettings, filename_suffix):
        # Export CSV
        csv_path = os.path.join(reportSettings.getReportDirectoryPath(), 'report-{}.csv'.format(filename_suffix))
        report = codecs.open(csv_path, 'w', encoding='utf-8')
        report.write('"search_type","search_term","match_term","match_path","keyword_list_name"\n')
        for each in list_of_hits:
            report.write(each.toCSV() + '\n')
        report.close()

         # Export JSON
        json_path = os.path.join(reportSettings.getReportDirectoryPath(), 'report-{}.json'.format(filename_suffix))
        report = codecs.open(json_path, 'w', encoding='utf-8')

        out_dict = {'source_program': 'autopsy' + ' ' + Version.getVersion(),                    
                    'creation': datetime.now().isoformat(), 
                    'keyword_hits': [x.toDict() for x in list_of_hits] }

        output_txt = json.dumps(out_dict, indent=4, sort_keys=True)
        report.write(output_txt) 
        report.flush()  
        report.close()

        # report.write('[' + '\n')
        # for each in list_of_hits:
        #     res = json.dumps(each.toDict())
        #     report.write(res + ',\n')

        # report.seek(-2, os.SEEK_END)    # This is a really bad hack. Need to fix properly!!!
        # report.truncate()
        # report.write(']' + '\n')
        # report.close()


    # https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename
    def get_valid_filename(self, name):
        #return "".join(x for x in name if x.isalnum())
        return "".join([x if x.isalnum() else "_" for x in name])
    
    def generateReport(self, reportSettings, progressBar):

        a = self.configPanel.getConfigValue()

        # Logging is currently broken. Logs to same path as when first run.        
        logging_path = reportSettings.getReportDirectoryPath() + 'logfile.txt'
        #logging.basicConfig(filename=logging_path, level=logging.INFO, encoding="utf-8")

        root_logger= logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(logging_path, 'w', 'utf-8') 
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')) 
        root_logger.addHandler(handler)

        progressBar.setIndeterminate(False)
        progressBar.start()
        progressBar.setMaximumProgress(8)
    
        fileName = os.path.join(reportSettings.getReportDirectoryPath(), self.getRelativeFilePath())
        logging.info('report path set to {}'.format(reportSettings.getReportDirectoryPath()))
        
        progressBar.updateStatusLabel("Extracting artefacts...")
        progressBar.increment()

        artefact_to_object_mappings = self.get_artefact_to_object_mappings()
    
        logging.debug('artefact_to_object_mappings:')
        logging.debug('============================')
        for each in artefact_to_object_mappings:
            logging.debug(each + ',' + artefact_to_object_mappings[each])

        # Get stuff from blackboard_attributes
        progressBar.updateStatusLabel("Extracting keyword hits...")

        list_of_hits = self.get_list_of_plain_keyword_hits()

        logging.debug('list_of_hits:')
        logging.debug('============================')
        for each in list_of_hits:
            logging.debug(each)

        files = self.get_file_list()    # performace optimisation possible here, don't need all files, just the ones with hits

        progressBar.updateStatusLabel("Updating extracted hits with file details...")

        progressBar.increment()

        # Updates the keyword hit list with values from the other tables
        for each in list_of_hits:
            each.aut_obj_id = artefact_to_object_mappings[each.aut_artefact_id]
            each.match_path = files[each.aut_obj_id]

        progressBar.increment()
        progressBar.updateStatusLabel("Separating keyword lists...")

        # This builds lists for each of the keyword LISTS so they can be exported separately
        list_of_keyword_list_names = {}
        for each in list_of_hits:
            if each.keyword_list_name != "":
                if each.keyword_list_name not in list_of_keyword_list_names:
                    list_of_keyword_list_names[each.keyword_list_name] = [each,]
                else:
                    list_of_keyword_list_names[each.keyword_list_name].append(each)

        progressBar.increment()

        progressBar.updateStatusLabel("Separating keyword hits...")

        # This builds lists for each of the KEYWORDS so they can be exported separately
        list_of_keywords = {}
        for each in list_of_hits:
            if each.keyword_list_name == "":
                if each.search_term not in list_of_keywords:
                    list_of_keywords[each.search_term] = [each,]
                else:
                    list_of_keywords[each.search_term].append(each)

        progressBar.increment()
        progressBar.updateStatusLabel("Generating reports...")

        # Generate CSV and JSON Reports
        self.generate_csv_and_json_reports(list_of_hits, reportSettings, 'all')

        # Generate separate output for each of the keyword lists
        for each in list_of_keyword_list_names:
            clean_name = self.get_valid_filename(each)
            self.generate_csv_and_json_reports(list_of_keyword_list_names[each], reportSettings, "LIST-" + clean_name)

        progressBar.increment()

        # Generate separate output for each of the keywords
        for each in list_of_keywords:
            clean_name = self.get_valid_filename(each)
            self.generate_csv_and_json_reports(list_of_keywords[each], reportSettings, "KW-" + clean_name)

        progressBar.increment()


        # Export debug
        debug_path = os.path.join(reportSettings.getReportDirectoryPath(), 'debug.txt')
        report = codecs.open(debug_path, 'w',  encoding='utf-8')
        report.write("\nFiles\n\n")
        for each in files:
            report.write(each + ":" + files[each] + '\n')
        report.write("\nAutopsy Internal Mappings\n\n")
        for each in artefact_to_object_mappings:
            report.write(each + ":" + artefact_to_object_mappings[each] + '\n')
        report.write("\nList of keyword lists\n\n")
        for each in list_of_keyword_list_names:
            report.write(each + '\n')

        report.close()

        progressBar.increment()

        # Add the report to the Case, so it is shown in the tree
        #Case.getCurrentCase().addReport(csv_path, self.moduleName, "Keyword Search Export CSV")
        #Case.getCurrentCase().addReport(json_path, self.moduleName, "Keyword Search Export JSON")

        # Call this with ERROR if report was not generated
        progressBar.complete(ReportStatus.COMPLETE)

        # close loggers
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()



class KW_ConfigPanel(JPanel):
    #numThreads = 8
    config_value = True

    def __init__(self):

        self.initComponents()
        self.config_value = True

    def initComponents(self):
        self.setLayout(GridBagLayout())

#        gbc = GridBagConstraints()
#        gbc.anchor = GridBagConstraints.NORTHWEST
#        gbc.gridx = 0
#        gbc.gridy = 0

#        descriptionLabel = JLabel("Keyword Export Configuration")
#        self.add(descriptionLabel, gbc)

#        gbc.gridy = 1
#        self.cbNSLookup = JCheckBox("Test", actionPerformed=self.cbNSLookupActionPerformed)
#        self.cbNSLookup.setSelected(True)
#        self.add(self.cbNSLookup, gbc)

        #self.dataList_Box_LB = ("Chocolate", "Ice Cream", "Apple Pie", "Pudding", "Candy" )
        #self.List_Box_LB = JList( self.dataList_Box_LB, valueChanged=self.onchange_lb)
        #self.List_Box_LB.setVisibleRowCount( 3 ) 
        #self.scpList_Box_LB = JScrollPane( self.List_Box_LB ) 
        #self.add( self.scpList_Box_LB ) 

    def getConfigValue(self):
        return self.config_value

    def cbNSLookupActionPerformed(self, event):
        source = event.getSource()

        if(source.isSelected()):
             self.config_value = True
        else:
             self.config_value = False