#!/usr/bin/env python
'''
    OSC Listen
        This is the OSC Listen Module.  It conatins all functions and properties for OSC Listen.
'''

# Import modules
from argparse import ArgumentParser
from liblo import Server, ServerError
from sys import exit
from os.path import isfile


# Global enumeration indicies constants
ENUMERATE_ITERATE_INDEX = 0
ENUMERATE_VALUE_INDEX = 1

# Declare class variables
exitCall = False
oscListenServers = []

class ConfigFile():
    """Load and parse OSC Toolkit configuration file for OSC Listen."""
    ## Class variables for loading and parsing the configuration file
    # Declare config constants
    CONFIG_PROPERTY_ARG = 0
    CONFIG_VALUE_ARG = 1
    CONFIG_PROTO_COMMENT = 0
    CONFIG_COMMENT_SYMBOL = '#'
        
    
    def __init__(self, configFileLocations):
        # config variabless with default values
        self.verboseListenPorts = False
        self.verboseMotd = False
        self.listenPorts = []
        self.motd = ''
    
        # Run initialization functions
        self.configData = self.parseConfigFile(self.loadConfigFile(configFileLocations))
        
    def loadConfigFile(self, configFileLocations):
        ## Load Config File
        for checkConf in configFileLocations:
            if isfile(checkConf):
                configFileLocation = checkConf
                break
        configFile = open(configFileLocation, 'r')
        configFileLines = configFile.read().split('\n')
        configFile.close()
        return configFileLines
    
    def parseConfigFile(self, configLines):
    # Parse config file lines
        for lineRead in configLines:
            if lineRead:
                lineReadProtoComment = lineRead.split(self.CONFIG_COMMENT_SYMBOL)[self.CONFIG_PROTO_COMMENT].split(' ')
                # Verbosity Settings
                if lineReadProtoComment[self.CONFIG_PROPERTY_ARG] == 'osclisten.verbose_listen_ports':
                    self.verboseListenPorts = bool(int(lineReadProtoComment[self.CONFIG_VALUE_ARG]))
                    
                if lineReadProtoComment[self.CONFIG_PROPERTY_ARG] == 'osclisten.verbose_motd':
                    self.verboseMotd = bool(int(lineReadProtoComment[self.CONFIG_VALUE_ARG]))

                if lineReadProtoComment[self.CONFIG_PROPERTY_ARG] == 'osclisten.motd':
                    for configArg in range(self.CONFIG_VALUE_ARG, len(lineReadProtoComment)):
                        self.motd += lineReadProtoComment[configArg] + ' '
            
                # OSC Settings
                if lineReadProtoComment[self.CONFIG_PROPERTY_ARG] == 'osclisten.listen_port':
                    self.listenPorts.append(int(lineReadProtoComment[self.CONFIG_VALUE_ARG]))

        return {'verboseListenPorts': self.verboseListenPorts, 
                'listenPorts': self.listenPorts, 
                'verboseMotd': self.verboseMotd, 
                'motd': self.motd}


class ParseArgs():
    """Parse command line arguments for OSC Listen"""

    def __init__(self):
        # argument vars with default values
        '''
            These should be overwritting the config file, and needs to be fixed.
            Load the default values from the config file dictionary.
        '''
        self.verboseListenPorts = False
        self.verboseMotd = False
        self.listenPorts = []

        # run initilization methods
        self.argData = self.parse()

    def parse(self):
        ## Parse Arguments
        # These values may potentially overwrite config arguments
        parser = ArgumentParser(description = 'Display incoming Open Sound Control messages.')

        ## Add arguments
        # List additional listen ports
        parser.add_argument(
                "-l",
                "--listen", 
                dest = "ports", 
                nargs = "+", 
                type = int, 
                help = "List additional ports to listen for OSC messages on.",
                )

        # Verbosely display listen ports
        parser.add_argument(
                "-v", 
                "--verbose", 
                action = "store_true", 
                help = "Verbosely display listen ports and MOTD on startup.",
                )

        # Add specific verbosity for listen ports and MOTD (see as OSC Whispers arg parsing)
        # Add quiet mode to halt verbosity
        # Add specific quiet mode (see OSC Whispers arg parsing)

        # Set argument vars
        args = parser.parse_args()
        if args.verbose:
            self.verboseListenPorts = self.verboseMotd = args.verbose
        if args.ports:
            for port in args.ports:
                self.listenPorts.append(port)
        
        return {
                'verboseListenPorts': self.verboseListenPorts,
                'verboseMotd': self.verboseMotd, 
                'listenPorts': self.listenPorts,
                }
        
    
# Verbosely display listen ports
def displayListenPorts(listenPorts):
    for portIdNum in listenPorts:
        print('Listening for OSC on port number: ', end = '')
        print(portIdNum)
    print()
    return
            
    
# Setup listen ports
def setupOSCServers(listenPorts):
    try:
        for oscServerId in listenPorts:
            oscListenServers.append(Server(oscServerId))
    except ServerError as  error:
        exit(error)
    return


# Build the functions for echoing messages on each port, then regiter as OSC servers
def buildOSCServers(listenPorts):
    # Setup Constants for building OSC servers
    global EXIT_ARG_INDEX
    EXIT_ARG_INDEX = 0
    COMMAND_OSC_PATH = '/osclisten'
    EXIT_COMMAND_PATH = COMMAND_OSC_PATH + '/exit'

    # Setup variables for building the OSC servers
    oscSppDef = []
    oscSppRegistration = []

    # Build server per port (spp) fucntion strings
    for eachPort in listenPorts:
        oscSppDefLine = 'def oscServer_' + str(eachPort) + '(path, args):\n'
        #if the path is '/oscwhispers/exit, and the value is 1 then exit
        '''
            The COMMAND_OSC_PATH command parsing and execution should not happen here
                i.e.
                    /osclisten/exit (1 | True | !NULL)
                    should happen elsewhere
                    along with any other OSC Listen specific OSC commands

            Fix  this in future commits
        '''
        oscSppDefLine += '    if path == "'  + EXIT_COMMAND_PATH  +  '" and int(args[EXIT_ARG_INDEX]) == 1:\n'
        oscSppDefLine += '        exit()\n'
        oscSppDefLine += '    else:\n'
        # or else echo the incoming message
        oscSppDefLine += '        print("'+str(eachPort)+': ", end = "")\n'
        oscSppDefLine += '        print(path, end = " ")\n'
        oscSppDefLine += '        print(args)\n'
        oscSppDefLine += '    return'
        oscSppDef.append(oscSppDefLine)

    # Build server per port (spp) functions
    for execSppDefLine in oscSppDef:
        exec(execSppDefLine)

    # Build server per port (spp) OSC method registration string
    for eachPort in listenPorts:
        oscSppBuild = 'oscListenServers[eachMethod[ENUMERATE_ITERATE_INDEX]].add_method(None, None, oscServer_' + str(eachPort) + ')'
        oscSppRegistration.append(oscSppBuild)
    
    # Register methods for listening on each port as an OSC Server
    for eachMethod in enumerate(oscSppRegistration):
        exec(eachMethod[ENUMERATE_VALUE_INDEX])
    return

def displayMOTD(motd):
    # MOTD variables
    # Set this in config, and maybe on the fly with an argument
    print(motd)
    print()
    return
