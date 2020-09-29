@echo off
setlocal EnableDelayedExpansion

call conda activate carla

rem python scenario_generation\openSCENARIO_generator.py --number_scenarios 5

set /a counter=0
set dir=%cd%\generated_scenarios

for /f %%f in ('dir /b generated_scenarios') do (
    set FILE=%%f
    echo !FILE!
    pushd %SCENARIO_RUNNER_ROOT%
    start "Scenario_Runner" cmd /k "python scenario_runner.py --reloadWorld --openscenario %dir%\!FILE!"
    timeout /t 10
    start "Manual_Control" cmd /k "python manual_control.py -a --res 300x200 --episode !counter!"
    timeout /t 60 && taskkill /f /fi "windowtitle eq Scenario_Runner*"
    taskkill /f /fi "windowtitle eq Manual_Control*"
    set /a counter+=1
    popd
)