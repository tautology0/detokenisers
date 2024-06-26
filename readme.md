# Introduction
A selection of BASIC detokenisers for various 8-bit platforms, these have been written over a 30 year period and may not work in all cases.

Included are:

BBCdetokenise<br>
For the BBC micro and Electron, works from the raw files, they'll need to be extracted from a disc image first

C64detokenise<br>
For the C64, works from a VICE snapshot

CPCdetokenise<br>
For the Amstrad CPC, works from a snapshot

MZdetokenise, mz80adetokenise, mz80kdetokenise<br>
For the Sharp MZ-700, MZ-80A and MZ-80K, works from the .MZF files

Oricdetokenise<br>
For the Oric, works from the raw files

Specdetokenise<br>
For the ZX Spectrum, works from a SNA snapshot

# Usage
All of these are simple stream extractors - they go through the files as a stream and print out the results as they go, they take the file on the command line and write to stdout, e.g.:

```
specdetokenise game.sna
```

To redirect the output use the > operator as in:

```
specdetokenise game.sna > game.bas
```
