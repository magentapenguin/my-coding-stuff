@if exist .\%1.spec (
    @pyinstaller --onefile --clean ./%1.spec %*
) else (
    @pyinstaller --onefile --clean ./%1.pyw %*
    @pyinstaller --onefile --clean ./%1.py %*
)
@echo Cleaning up...
@rmdir .\build /s /q
@move .\dist\%1.exe .\%1.exe
@rmdir .\dist /s /q
@echo Done!