@echo off
:: DungeonDoor Windows 빌드 스크립트
:: 실행 전: pip install pyinstaller pygame-ce

echo [1/3] PyInstaller 설치 확인...
pip install pyinstaller --quiet

echo [2/3] 빌드 시작...
pyinstaller game.spec --clean --noconfirm

echo [3/3] 빌드 완료!
echo 결과물: dist\DungeonDoor\game.exe
pause
