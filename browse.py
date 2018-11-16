import os
import indexing.whooshPowers as wp

# Basic Outline

def getAdjacentPowersOf(power):
	return None

def getChildPowersOf(power):
	return None

def getParentPowersOf(power):
	return None 

#find power by exact index match
def getPowerData(power):
	return wp.getPower(power)

def tester():
	powername = "Flight"
	print(f"getting entry of power {powername}")
	wp.getPower(powername).printAll()
	