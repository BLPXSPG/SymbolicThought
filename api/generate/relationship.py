import os
from time import sleep
import json, csv
import yaml
#from memory.processing import split_text
from config.utils.token_counter import count_string_tokens
import shutil
#from googletrans import Translator
#from deep_translator import GoogleTranslator
import itertools
import re
from math import ceil
import logging


class Relation():
    def __init__(self, relation):
        self.relation = relation
        self.child_relation = []
        self.parent_relation = []
        self.inversion = []
        self.gender = ""
        self.exclusive = False
        self.conflict = []
        self.antisymmetric = []

    def add_child_relation(self, child_relation):
        self.child_relation.append(child_relation)

    def add_parent_relation(self, parent_relation):
        self.parent_relation.append(parent_relation)

    def add_inversion(self, inversion):
        self.inversion = inversion

    def add_gender(self, gender):
        self.gender = gender

    def add_conflict(self, conflict_list):
        self.conflict = conflict_list
    
    def add_antisymmetric(self, antisymmetric_list):
        self.antisymmetric = antisymmetric_list

    def update_exclusive(self, exclusive):
        if exclusive == "Y":
            self.exclusive = True

    def print_properties(self):
        return self.relation, self.child_relation, self.parent_relation, self.inversion, self.gender, self.conflict, self.antisymmetric
