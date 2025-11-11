@echo off
echo ================================================================================
echo PRIORITY TESTING SUITE
echo ================================================================================
echo.
echo This will run the test menu. Choose your test from the menu.
echo.
echo Press any key to start...
pause > nul

python run_tests.py

echo.
echo ================================================================================
echo Tests complete! Press any key to exit...
pause > nul
