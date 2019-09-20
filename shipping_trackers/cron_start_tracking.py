"""
script that will be a cronjob, called with the shipping tracking number at argv[1] by seller when he adds a shipping number
in the my contract page
it will call a function that will check for all the things written in the notes and update the shipping state of the object
"""
import sys

# get the contract address from the argument
shipping_number = sys.argv[1]

# call the method