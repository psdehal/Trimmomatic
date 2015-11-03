#BEGIN_HEADER
from biokbase.workspace.client import Workspace as workspaceService
import requests
import subprocess
import os
import sys
import re
#END_HEADER


class Trimmomatic:
    '''
    Module Name:
    Trimmomatic

    Module Description:
    A KBase module: Trimmomatic
This sample module contains one small method - count_contigs.
    '''

    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################
    #BEGIN_CLASS_HEADER
    workspaceURL = None
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.workspaceURL = config['workspace-url']
        #END_CONSTRUCTOR
        pass

    def count_contigs(self, ctx, workspace_name, contigset_id):
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN count_contigs
        token = ctx['token']
        wsClient = workspaceService(self.workspaceURL, token=token)
        contigSet = wsClient.get_objects([{'ref': workspace_name+'/'+contigset_id}])[0]['data']
        returnVal = {'contig_count': len(contigSet['contigs'])}
        #END count_contigs

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method count_contigs return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]

    def runTrimmomatic(self, ctx, input_params):
        # ctx is the context object
        # return variables are: report
        #BEGIN runTrimmomatic
        token = ctx['token']
        wsClient = workspaceService(self.workspaceURL, token=token)
        headers = {'Authorization': 'OAuth '+token}

        TrimmomaticCmd = 'java -jar /kb/module/Trimmomatic-0.33/trimmomatic-0.33.jar PE -phred33'
        TrimmomaticParams = 'ILLUMINACLIP:/kb/module/Trimmomatic-0.33/adapters/TruSeq3-PE.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36'
    

        try:
            pairedEndReadLibrary = wsClient.get_objects([{'name': input_params['input_paired_end_library'], 
                                                            'workspace' : input_params['input_ws']}])[0]
        except: 
            raise ValueError("Couldn't get object from workspace")

        if 'lib1' in pairedEndReadLibrary['data']:
            forward_reads = pairedEndReadLibrary['data']['lib1']['file']
        elif 'handle_1' in pairedEndReadLibrary['data']:
            forward_reads = pairedEndReadLibrary['data']['handle_1']

        if 'lib2' in pairedEndReadLibrary['data']:
            reverse_reads = pairedEndReadLibrary['data']['lib2']['file']
        elif 'handle_2' in pairedEndReadLibrary['data']:
            reverse_reads = pairedEndReadLibrary['data']['handle_2']

        forward_reads_file = open(forward_reads['file_name'], 'w', 0)


        r = requests.get(forward_reads['url']+'/node/'+forward_reads['id']+'?download', stream=True, headers=headers)
        for chunk in r.iter_content(1024):
            forward_reads_file.write(chunk)

        reverse_reads_file = open(reverse_reads['file_name'], 'w', 0)

        r = requests.get(reverse_reads['url']+'/node/'+reverse_reads['id']+'?download', stream=True, headers=headers)
        for chunk in r.iter_content(1024):
            reverse_reads_file.write(chunk)

        s = " "
        cmdstring = s.join( (TrimmomaticCmd, 
                            forward_reads['file_name'], 
                            reverse_reads['file_name'],
                            'forward_paired_'   +forward_reads['file_name'],
                            'forward_unpaired_' +forward_reads['file_name'],
                            'reverse_paired_'   +reverse_reads['file_name'],
                            'reverse_unpaired_' +reverse_reads['file_name'],
                            TrimmomaticParams) )

        cmdstring2 = "wc -l " + forward_reads['file_name']
        cmdProcess = subprocess.Popen(cmdstring2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        stdout, stderr = cmdProcess.communicate()
        report = "cmdstring: " + cmdstring + " stdout: " + stdout + " stderr " + stderr


        #END runTrimmomatic

        # At some point might do deeper type checking...
        if not isinstance(report, basestring):
            raise ValueError('Method runTrimmomatic return value ' +
                             'report is not type basestring as required.')
        # return the results
        return [report]
