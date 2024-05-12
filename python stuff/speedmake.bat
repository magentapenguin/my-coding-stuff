@if exist .\%1.spec (
    @pyinstaller --onefile --clean ./%1.spec %*
) else (
    @pyinstaller --onefile --clean ./%1.pyw %*
    @pyinstaller --onefile --clean ./%1.py %*
)
@echo Done!