#!/usr/bin/env python3
#This junk is designed to parse a FED dump of 1356 and 1405 for CICADA information
#It's... ad hoc. I wouldn't describe it as "robust". Or easy to read. It's a real piece of junk
import argparse
import re
from rich.console import Console
from rich.table import Table
import math
import ROOT

console = Console()

#Every event starts with "Begin processing the xth record"
#we split on that
#and then inside the resulting strings we start grabbing from the FED records
#This seems like the rickitiest set of ad-hoc RE's ever, but I'm jet lagged and can't think
def parseEvents(eventData):
    splitEvents = re.split(
        "Begin processing",
        eventData
    )
    splitEvents = splitEvents[1:] #First entry will be empty
    #Peel off everything at the start of the event
    #We know the event starts with "FED#", so we start there
    for index, event in enumerate(splitEvents):
        FEDInfo = re.search("FED#.*", event, re.DOTALL)
        if FEDInfo:
            FEDInfoString = FEDInfo.group(0)
        else:
            FEDInfoString = ''
        splitEvents[index] = FEDInfoString
    #Trim everything off the end. We know it's the end because it will be a double newline
    for index, event in enumerate(splitEvents):
        FEDInfo = re.search(".*(?=\n\n)", event, re.DOTALL)
        if FEDInfo:
            FEDInfoString = FEDInfo.group(0)
        else:
            FEDInfoString = ''
        splitEvents[index] = FEDInfoString
    #console.print(splitEvents)
    return splitEvents

def parseRLE(eventData):
    eventStrings = re.findall(
        'Run [0-9]+, Event [0-9]+, LumiSection [0-9]+',
        eventData,
    )
    RLETuples = []
    for eventString in eventStrings:
        RLE = re.findall(
            '[0-9]+',
            eventString
        )
        RLETuples.append(
            (
                int(RLE[0]),
                int(RLE[1]),
                int(RLE[2]),
            )
        )
    return RLETuples

def splitLine(line):
    splitLine = line.split(' ')
    lineNum = splitLine[0]
    firstWord = splitLine[2][:8]
    secondWord = splitLine[2][8:]
    return lineNum, firstWord, secondWord

def convertBitsToCICADAScore(hexWord):
    firstChar = int(hexWord[0], 16)
    firstChar = firstChar << 4
    secondChar = int(hexWord[1], 16)
    thirdChar = int(hexWord[2], 16)
    thirdChar = thirdChar * math.pow(2.0, -4)
    fourthChar = int(hexWord[3], 16)
    fourthChar = fourthChar * math.pow(2.0, -8)

    result = float(firstChar) + float(secondChar) + float(thirdChar) + float(fourthChar)
    return result

def parseFED1356(eventData):
    console.print("FED #1356")
    console.print()
    
    FED1356Data = eventData.split('\nFED# 1405')[0]
    FED1356Data = FED1356Data.split('\n')[1:]

    CICADASection = ''
    
    for line in FED1356Data:
        #This is deliberately flipped word order
        #We read these words right to left in the DAQ
        lineNum, secondWord, firstWord = splitLine(line)
        if lineNum == '0161': # header line
            BCID = secondWord[-3:]

            CICADASection += line+'\n'
        if lineNum == '0162': #first CICADA line
            CICADAWord_1 = firstWord
            CICADAWord_2 = secondWord

            CICADABits_1 = CICADAWord_1[0]
            CICADABits_2 = CICADAWord_2[0]
            
            CICADASection += line+'\n'
        if lineNum == '0163': #second CICADA line
            CICADAWord_3 = firstWord
            CICADAWord_4 = secondWord
            
            CICADABits_3 = CICADAWord_3[0]
            CICADABits_4 = CICADAWord_4[0]
            
            CICADASection += line+'\n'
        if lineNum == '0164': #third CICADA line
            CICADAWord_5 = firstWord
            CICADAWord_6 = secondWord
            
            CICADASection += line+'\n'

    console.print()
    console.print('CICADA Section + Header') 
    console.print()
    console.print(CICADASection)

    CICADABits = CICADABits_1 + CICADABits_2 + CICADABits_3 + CICADABits_4
    CICADAWords = f'{CICADAWord_1} {CICADAWord_2} {CICADAWord_3} {CICADAWord_4} {CICADAWord_5} {CICADAWord_6}'
    CICADADecimal = convertBitsToCICADAScore(CICADABits)
    
    outputGrid = Table()
    outputGrid.add_column('BCID (decimal)', style='cyan')
    outputGrid.add_column('BCID (hex)', style='cyan')
    outputGrid.add_column('CICADA (decimal)', style='green')
    outputGrid.add_column('CICADA (hex)', style='green')
    outputGrid.add_column('Event Words')
    outputGrid.add_row(f'{int(BCID, 16)}', f'{BCID}', f'{CICADADecimal}', CICADABits, CICADAWords)
    console.print(outputGrid)
    console.print()

def parseFED1405(eventData):
    console.print("FED #1405")
    console.print()
    FED1405Data = eventData.split('\nFED# 1405')[1]
    FED1405Data = FED1405Data.split('\n')[1:]

    #Okay, CICADA data is at an indeterminate spot in uGT marked by a "161e" to start
    # and ended by an "181e"
    firstIndex = None
    secondIndex = None

    for index, line in enumerate(FED1405Data):
        if '161e' in line:
            firstIndex = index
        elif '181e' in line:
            secondIndex = index
    if firstIndex == None or secondIndex == None:
        console.log(":emoji-warning: failed to find proper CICADA data in FED# 1405, skipping.")
        return
    FED1405Data=FED1405Data[firstIndex:secondIndex+1]
    CICADALines = FED1405Data[1:-1]
    
    CICADASection = ''
    for line in FED1405Data:
        CICADASection+=line+'\n'

    CICADAWords = {}
    CICADABits = {}
    CICADAScores = {}
    for lineIndex, line in enumerate(CICADALines):
        BX = (lineIndex // 3) -2
        lineNum, secondWord, firstWord = splitLine(line) #like FED #1356 we read left to right
        if BX not in CICADAWords:
            CICADAWords[BX] = []
            CICADABits[BX] = ''
            CICADAScores[BX] = 0.0
            
        if lineIndex % 3 == 0: #First CICADA line
            firstCICADAWord = firstWord
            secondCICADAWord = secondWord
            CICADAWords[BX].append(firstCICADAWord)
            CICADAWords[BX].append(secondCICADAWord)

            CICADABits_1 = firstCICADAWord[0]
            CICADABits_2 = secondCICADAWord[0]
            CICADABits[BX] += CICADABits_1+CICADABits_2

        elif lineIndex % 3 == 1: #Second CICADA line
            thirdCICADAWord = firstWord
            fourthCICADAWord = secondWord
            CICADAWords[BX].append(thirdCICADAWord)
            CICADAWords[BX].append(fourthCICADAWord)

            CICADABits_3 = thirdCICADAWord[0]
            CICADABits_4 = fourthCICADAWord[0]
            CICADABits[BX] += CICADABits_3+CICADABits_4

        else:
            fifthCICADAWord = firstWord
            sixthCICADAWord = secondWord
            CICADAWords[BX].append(fifthCICADAWord)
            CICADAWords[BX].append(sixthCICADAWord)            
    
    console.print('CICADA Section + Header + Trailer')
    console.print()
    console.print(CICADASection)

    outputTable = Table()
    outputTable.add_column("BX", style='cyan')
    outputTable.add_column('CICADA (decimal)', style='green')
    outputTable.add_column('CICADA (hex)', style='green')
    outputTable.add_column('Event Words')
    for BX in CICADAWords:
        CICADAScores[BX] = convertBitsToCICADAScore(CICADABits[BX])
        EventWords = ' '.join(CICADAWords[BX])
        outputTable.add_row(
            f'{BX}',
            f'{CICADAScores[BX]}',
            f'{CICADABits[BX]}',
            EventWords,
        )
    console.print(outputTable)

def isValidCICADAScore(score):
    fixedPointValue = int(score * (1<<8))
    reconstruction = float(fixedPointValue)/(1<<8)
    return reconstruction == score
    
def convertCICADAScoreToHex(score):
    if not isValidCICADAScore(score):
        console.print(":emoji-warning: [red]Emulator CICADA score appeared not to be a 16 bit fixed point number. Returning null hex[/red]")
        return ''
    fixedValue = int(score * (1<<8))
    hexValue = hex(fixedValue)
    hexValue = hexValue.split('x')
    hexValue = hexValue[0]+'x'+'0'*(4-len(hexValue[1]))+hexValue[1]
    return hexValue
    
def dumpEmulatorInfo(theFile, index):
    #theFile.ls()
    theTree = theFile.l1CaloSummaryEmuTree.L1CaloSummaryTree
    #theTree.Print()
    theTree.GetEntry(index)
    console.print()
    console.print('Emulator')
    console.print()
    theScore = theTree.CaloSummary.CICADAScore
    console.print(f'Score: [green]{theScore:>12.8f}[/green]')
    #console.print(f'Hex: [green]{theScore.hex():>14}[/green]')
    CICADAHex = convertCICADAScoreToHex(theScore)
    console.print(f'Hex: [green]{CICADAHex:>14}[/green]')
    console.print()

    console.print('Model Input:')
    theInputArray = theTree.CaloSummary.modelInput
    modelInputLeaf = theTree.GetLeaf('modelInput')
    inputGrid = []
    for iphi in range(18):
        iPhiSlice = []
        for ieta in range(14):
            iPhiSlice.append(
                int(modelInputLeaf.GetValue(iphi*14 + ieta))
            )
        inputGrid.append(iPhiSlice)
    #console.print(inputGrid)
    #displayGrid = Table.grid()
    displayGrid = Table(show_lines=True)
    displayGrid.add_column("iPhi / iEta")
    for ieta in range(14):
        displayGrid.add_column(
            f'[cyan]{ieta}[/cyan]',
            justify='center',
            #min_width=3,
            #style='black on white' if ieta%2==0 else None
        )
    for iphi in range(18):
        displayGrid.add_row(
            f'[cyan]{17-iphi}[/cyan]',
            *[
                f'{inputGrid[17-iphi][ieta]}' for ieta in range(14)
            ]
        )
    console.print(displayGrid)

def dumpEvent(index, eventData, runTuple, rootFile):
    console.rule(f'Run: {runTuple[0]:>10d}, Event: {runTuple[1]:>10d}')
    #console.print(eventData)
    parseFED1356(eventData)
    parseFED1405(eventData)

    if rootFile is not None:
        dumpEmulatorInfo(rootFile, index)

def main(args):
    with open(args.file) as theFile:
        data = theFile.read()
    #Okay, our first job is to parse this set of nonsense into a set of events we can read
    runs = parseRLE(data)
    console.print(f'Processed {len(runs):>6d} FED dumps')
    eventData = parseEvents(data)
    if len(runs) != len(eventData):
        console.log(":emoji-warning: Got a different number of parsed event numbers than parsed events")
        exit(1)

    rootFile = None
    if args.l1Ntuple is not None:
        rootFile = ROOT.TFile(args.l1Ntuple)
    #do the magic
    for index in range(len(eventData)):
        dumpEvent(index, eventData[index], runs[index], rootFile)
    #Then, for each event, we try to parse out FED #1356 and FED #1405 info

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Dump FED 1356 & 1405 CICADA information")
    parser.add_argument(
        '--file',
        required=True,
        nargs='?',
        help='FED dump text file to dump out'
    )
    parser.add_argument(
        '--l1Ntuple',
        nargs='?',
        help='L1 Ntuple of the corresponding events to print inputs and outputs from the emulator'
    )

    args = parser.parse_args()
    main(args)
