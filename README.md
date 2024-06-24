## Basic usage
### Make the FED Dump
```
cmsRun fedDumpingTool/dumpFEDInfoFromRAW.py feds=1356,1405 inputFiles=/store/data/Run2024F/ZeroBias/RAW/v1/000/382/256/00000/ede7d1ac-2b3d-4496-82d5-6d1bf636d7ff.root maxEvents=10 >& Run382256_FED1356_FED1405_10Events.log
```

### Parse information
```
python3 parseFEDDump.py --file Run382256_FED1356_FED1405_10Events.log
```