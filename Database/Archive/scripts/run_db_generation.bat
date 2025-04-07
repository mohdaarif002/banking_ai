@echo off
echo Running enhanced database generation script...
call activate docgen11
python enhanced_create_mockdata.py
echo Done! 