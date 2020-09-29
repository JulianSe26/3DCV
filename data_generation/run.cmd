@echo off
call conda activate carla

python scenario_generation\openSCENARIO_generator.py --number_scenarios 5

set counter=0
for /f %%f in ('dir /b .\generated_scenarios') do (
    echo %%f
    set file=%cd%\generated_scenarios\%%f
    pushd %SCENARIO_RUNNER_ROOT%
    start cmd /k "python manual_control.py -a --res 300x200 --episode %counter%"
    python scenario_runner.py --openscenario %file%
    set counter=%counter% + 1
    popd
)