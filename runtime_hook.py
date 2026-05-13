"""PyInstaller 런타임 훅: frozen 환경에서 작업 디렉토리를 exe 위치로 설정."""
import os
import sys

if getattr(sys, 'frozen', False):
    # exe가 있는 폴더를 기준 디렉토리로 설정
    # (세이브/설정 파일이 exe 옆에 생성되도록)
    os.chdir(os.path.dirname(sys.executable))
