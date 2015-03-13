'''
Created on Feb 8, 2015

@author: Rob
'''
import re
class StringFixer(object):
    '''
    Just simplifying shit a bit.
    '''

    def __init__(self, pattern, replacement=''):
        self.pattern=re.compile(pattern,flags=re.IGNORECASE)
        self.replacement=replacement
        
    def Fix(self, string):
        return self.pattern.sub(self.replacement,string)