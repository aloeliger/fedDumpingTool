import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

process = cms.Process("FEDDUMP")

# Read command line arguments
options = VarParsing('analysis')
options.register(
    'feds',
    [],
    VarParsing.multiplicity.list,
    VarParsing.varType.int,
    'FEDS to create dumped information for'
)

options.parseArguments()

process.source = cms.Source(
    'PoolSource',
    fileNames = cms.untracked.vstring(options.inputFiles),
)

# limit to maximum events
process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(options.maxEvents),
)

# Seems like we don't get full fed dumps for every event
# This prevents the tool from erroring out, and moves on to the next event
process.options = cms.untracked.PSet(
    TryToContinue = cms.untracked.vstring('ProductNotFound')
)


# Get the analyzers necssary to dump fed info
process.GlobalNumbersAnalysis = cms.EDAnalyzer('GlobalNumbersAnalysis')
process.DumpFEDRawDataProduct = cms.EDAnalyzer(
    'DumpFEDRawDataProduct',
    label = cms.untracked.InputTag('rawDataCollector'),
    feds = cms.untracked.vint32(options.feds),
    dumpPayload = cms.untracked.bool(True),
)

process.p = cms.Path(process.GlobalNumbersAnalysis+process.DumpFEDRawDataProduct)
