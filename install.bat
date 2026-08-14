@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "REPO_ROOT=%~dp0"
set "TARGET=both"
set "METHOD=symlink"
set "FORCE=false"
set "DRY_RUN=false"
set /a SKILL_COUNT=0

:parse_args
if "%~1"=="" goto validate_args

if /I "%~1"=="--target" (
    if "%~2"=="" goto missing_target
    set "TARGET=%~2"
    shift
    shift
    goto parse_args
)

if /I "%~1"=="--method" (
    if "%~2"=="" goto missing_method
    set "METHOD=%~2"
    shift
    shift
    goto parse_args
)

if /I "%~1"=="--skill" (
    if "%~2"=="" goto missing_skill
    call :add_skill "%~2"
    shift
    shift
    goto parse_args
)

if /I "%~1"=="--force" (
    set "FORCE=true"
    shift
    goto parse_args
)

if /I "%~1"=="--dry-run" (
    set "DRY_RUN=true"
    shift
    goto parse_args
)

if /I "%~1"=="-h" goto usage_success
if /I "%~1"=="--help" goto usage_success

echo Unknown argument: %~1 1>&2
call :usage 1>&2
exit /b 2

:missing_target
echo Missing value for --target 1>&2
exit /b 2

:missing_method
echo Missing value for --method 1>&2
exit /b 2

:missing_skill
echo Missing value for --skill 1>&2
exit /b 2

:validate_args
if /I "%TARGET%"=="codex" goto target_valid
if /I "%TARGET%"=="claude" goto target_valid
if /I "%TARGET%"=="both" goto target_valid
echo --target must be codex, claude, or both 1>&2
exit /b 2

:target_valid
if /I "%METHOD%"=="symlink" goto method_valid
if /I "%METHOD%"=="copy" goto method_valid
echo --method must be symlink or copy 1>&2
exit /b 2

:method_valid
if defined CODEX_HOME (
    set "CODEX_HOME_EFFECTIVE=%CODEX_HOME%"
) else (
    set "CODEX_HOME_EFFECTIVE=%USERPROFILE%\.codex"
)

if defined CLAUDE_HOME (
    set "CLAUDE_HOME_EFFECTIVE=%CLAUDE_HOME%"
) else (
    set "CLAUDE_HOME_EFFECTIVE=%USERPROFILE%\.claude"
)

if not "%SKILL_COUNT%"=="0" goto skills_ready
for /D %%D in ("%REPO_ROOT%*") do if exist "%%~fD\SKILL.md" call :add_skill "%%~nxD"

:skills_ready
if not "%SKILL_COUNT%"=="0" goto install_skills
echo No skill folders with SKILL.md found in %REPO_ROOT% 1>&2
exit /b 1

:install_skills
for /L %%I in (1,1,%SKILL_COUNT%) do (
    call :install_selected %%I
    if errorlevel 1 exit /b 1
)

echo Done.
exit /b 0

:add_skill
set /a SKILL_COUNT+=1
set "SKILL_%SKILL_COUNT%=%~1"
exit /b 0

:install_selected
call set "CURRENT_SKILL=%%SKILL_%~1%%"

if /I "%TARGET%"=="codex" goto install_codex_only
if /I "%TARGET%"=="claude" goto install_claude_only

call :install_skill "Codex" "%CODEX_HOME_EFFECTIVE%" "%CURRENT_SKILL%"
if errorlevel 1 exit /b 1
call :install_skill "Claude" "%CLAUDE_HOME_EFFECTIVE%" "%CURRENT_SKILL%"
if errorlevel 1 exit /b 1
exit /b 0

:install_codex_only
call :install_skill "Codex" "%CODEX_HOME_EFFECTIVE%" "%CURRENT_SKILL%"
exit /b %ERRORLEVEL%

:install_claude_only
call :install_skill "Claude" "%CLAUDE_HOME_EFFECTIVE%" "%CURRENT_SKILL%"
exit /b %ERRORLEVEL%

:install_skill
setlocal
set "AGENT_LABEL=%~1"
set "AGENT_HOME=%~2"
set "SKILL=%~3"
set "SRC=%REPO_ROOT%%~3"
set "DEST=%~2\skills\%~3"

if exist "%SRC%\SKILL.md" goto source_valid
echo Skill not found: %SRC% 1>&2
exit /b 1

:source_valid
echo Installing %SKILL% for %AGENT_LABEL%
echo   source: %SRC%
echo   target: %DEST%
echo   method: %METHOD%

if /I "%DRY_RUN%"=="true" exit /b 0

if not exist "%AGENT_HOME%\skills" mkdir "%AGENT_HOME%\skills"
if errorlevel 1 (
    echo Could not create skills directory: %AGENT_HOME%\skills 1>&2
    exit /b 1
)

if not exist "%DEST%" goto create_install

set "RS_INSTALL_DEST=%DEST%"
set "RS_INSTALL_SRC=%SRC%"
powershell.exe -NoLogo -NoProfile -NonInteractive -Command "$item = Get-Item -LiteralPath $env:RS_INSTALL_DEST -Force -ErrorAction SilentlyContinue; if ($item -and $item.LinkType -and ([IO.Path]::GetFullPath([string]$item.Target) -eq [IO.Path]::GetFullPath($env:RS_INSTALL_SRC))) { exit 0 } else { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo   already linked
    exit /b 0
)

if /I not "%FORCE%"=="true" (
    echo Destination exists. Re-run with --force to replace: %DEST% 1>&2
    exit /b 1
)

set "TIMESTAMP="
for /F "usebackq delims=" %%T in (`powershell.exe -NoLogo -NoProfile -NonInteractive -Command "Get-Date -Format yyyyMMddHHmmss"`) do set "TIMESTAMP=%%T"
if not defined TIMESTAMP set "TIMESTAMP=%RANDOM%%RANDOM%"
set "BACKUP=%DEST%.backup-%TIMESTAMP%"
move "%DEST%" "%BACKUP%" >nul
if errorlevel 1 (
    echo Could not back up existing destination: %DEST% 1>&2
    exit /b 1
)
echo   backup: %BACKUP%

:create_install
if /I "%METHOD%"=="copy" goto copy_skill

mklink /D "%DEST%" "%SRC%" >nul
if errorlevel 1 (
    echo Could not create the directory symlink. Enable Windows Developer Mode, 1>&2
    echo run Command Prompt as Administrator, or use --method copy. 1>&2
    exit /b 1
)
exit /b 0

:copy_skill
xcopy "%SRC%" "%DEST%\" /E /I /H /K /Y >nul
if errorlevel 1 (
    echo Could not copy skill to: %DEST% 1>&2
    exit /b 1
)
exit /b 0

:usage_success
call :usage
exit /b 0

:usage
echo Install research skills for Codex and/or Claude.
echo.
echo Usage:
echo   install.bat [--target codex^|claude^|both] [--method symlink^|copy] [--skill NAME] [--force] [--dry-run]
echo.
echo Defaults:
echo   --target both
echo   --method symlink
echo   --skill all folders in this repo that contain SKILL.md
echo.
echo Examples:
echo   install.bat
echo   install.bat --target codex
echo   install.bat --method copy --force
echo   install.bat --skill create-dl-project --target both
echo.
echo Environment:
echo   CODEX_HOME   Defaults to %%USERPROFILE%%\.codex
echo   CLAUDE_HOME  Defaults to %%USERPROFILE%%\.claude
exit /b 0
