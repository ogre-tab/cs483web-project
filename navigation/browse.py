import ntpath
import os
import signal
import sqlite3
import sys

import whooshPowers as SPIndex

from whoosh.fields import ID, TEXT, Schema
from whoosh.index import Index, create_in, exists_in, open_dir
from whoosh.qparser import MultifieldParser

SPIndex.checkAndLoadIndex()

# Basic Outline

def getAdjacentPowersOf(power):
	return None

def getChildPowersOf(power):
	return None

def getParentPowersOf(power):
	return None 
	
