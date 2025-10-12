:: this @echo off prevents the command window from showing up
:: by add @ at the beginning of the line the command itself is not printed
@echo off

:: %~dp0 stands for "drive and path of this script"
:: %* stands for "all the arguments passed to this script"
:: so this line runs gitgo.py located in the same folder as this .bat file
py "%~dp0gitgo.py" %*