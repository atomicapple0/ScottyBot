import ScottyBot
import sys
import argparse
from build import build_courses

def main():
    cmd = sys.argv[1]
    if len(sys.argv) > 1:
        args = sys.argv[2:]
    else:
        args = None
    if cmd == '-u': # update course descriptions json files
        build_courses(args)
        ScottyBot.buildFce()
    elif cmd == '-f': # get fce info
        ScottyBot.fce(args)
    elif cmd == '-c': # get courses info
        ScottyBot.course(args[0]) 
    
if __name__ == "__main__":
    main()
