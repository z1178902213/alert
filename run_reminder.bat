@echo off
chcp 65001 >nul
title 思源笔记提醒器
echo 正在启动思源笔记提醒器...
echo.

REM 尝试多种Python命令
set PYTHON_CMD=
for %%i in (python py python3) do (
    %%i --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=%%i
        goto :found_python
    )
)

REM 尝试从PATH中查找Python
where python >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :found_python
)

REM 尝试常见的Python安装路径
for %%i in (
    "C:\Python*\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python*\python.exe"
    "C:\Program Files\Python*\python.exe"
    "C:\Program Files (x86)\Python*\python.exe"
) do (
    if exist %%i (
        set PYTHON_CMD=%%i
        goto :found_python
    )
)

:python_not_found
echo 错误：未找到Python环境！
echo.
echo 请按以下步骤安装Python：
echo 1. 访问 https://www.python.org/downloads/
echo 2. 下载最新版本的Python（推荐Python 3.8+）
echo 3. 安装时请勾选"Add Python to PATH"选项
echo 4. 安装完成后重启命令提示符
echo.
echo 或者双击"启动说明.txt"查看详细说明
echo.
pause
exit /b 1

:found_python
echo 检测到Python：%PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM 检查tkinter是否可用
echo 检查tkinter库...
%PYTHON_CMD% -c "import tkinter; print('tkinter库可用')" >nul 2>&1
if errorlevel 1 (
    echo 警告：tkinter库不可用，程序可能无法正常运行
    echo 这通常是因为Python安装不完整
    echo.
    set /p CONTINUE="是否继续运行？(y/n): "
    if /i not "!CONTINUE!"=="y" (
        echo 程序已取消
        pause
        exit /b 1
    )
)

REM 检查alert.py文件是否存在
if not exist "alert.py" (
    echo 错误：未找到alert.py文件！
    echo 请确保批处理文件与alert.py在同一目录下
    pause
    exit /b 1
)

echo 启动提醒器...
echo 程序启动后，您可以：
echo - 关闭主窗口，程序将在后台继续运行
echo - 通过任务管理器找到并结束程序进程
echo.

REM 运行程序
%PYTHON_CMD% alert.py

REM 如果程序异常退出，等待用户确认
if errorlevel 1 (
    echo.
    echo 程序异常退出，错误代码：%errorlevel%
    echo 请检查错误信息或查看README.md文件
    pause
) 