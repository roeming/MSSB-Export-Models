MSSB Character Model Extractor v 1.0

This program will extract all character models from Mario Superstar Baseball

Please extract your ZZZZ.dat, aaaa.dat, and main.dol and put them in the extractor/data folder.
Make sure you have python installed, you can then double click run.bat to install the needed python libraries, and run the main program
Alternatively, you can run `python main.py` while in the extractor folder

The outputted files will be in the extractor/outputs folder.

If you want to name a file, add the name and location to the FileNames.json file. The 'Location' tag will be the folder name you wish to rename.

Let me (Roeming#8394 on discord) know if anything fails

Notes:

Bat and ball models are grouped into the hand models, but due to quantization, don't appear right yet.

No animations or bones are currently extracted, that is in the works.

Normals may be strange, so you might want to recalculate those in blender.
