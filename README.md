### Overview
This repository contains a script to demonstrate the lockup resulting from Statsig SDK thread panicking in a forked process during init for version `0.5.0`. The panic can also be reproduced in version `0.4.2`, but it does not cause a lockup. 

The script runs a main thread with initialized Statsig. 
It then forks multiple times, shutting the SDK down before each fork and reinitializing after each fork. 
The forks also initialize Statsig after being created. 
The parent thread and the forks each end up with their own instance of Statsig. 

The process continues until stopped. Logs are written to `repro.log` in the current directory.


### Setup
1. Clone the repo 

2. Create a `.env` at the repo root with your development Statsig SDK key:

   ```env
   STATSIG_SERVER_SDK_KEY=<your_dev_statsig_sdk_key>
   ```

3. Install `pyenv`

    ```shell
    brew install pyenv pyenv-virtualenv
    
    eval "$(pyenv init --path)"
    eval "$(pyenv virtualenv-init -)"
    ```

4. Install the virtual environment

    ```shell
    pyenv install 3.10.9
    pyenv virtualenv 3.10.9 klaviyo-statsig-panic-repro
    pyenv local klaviyo-statsig-panic-repro
    ```

5. Install the requirements

    ```shell
    pip install -r requirements.txt
    ```
   
6. Run the repro script
    ```shell
    python repro.py
    ```


### Symptoms
After a few minutes, Statsig will panic in one of the forked processes. 

#### Version `0.5.0`
The thread panic is accompanied by the following log message:

```
WARN  [Statsig::StatsigRuntime] Attempt to shutdown runtime from inside runtime
```

![lockup_in_logs.png](images/lockup_in_logs.png)

The script will keep checking the fork status for up to 5 minutes, killing all forks if the timeout is exceeded. To increase the timeout, modify the `timeout` variable in `repro.py`.
During the hang-up (within those 5 minutes), we can use `py-spy` or other profiling software to inspect the hanging process and see that Python is stuck waiting for the Statsig SDK to finish initializing:

```shell
sudo py-spy dump --subprocesses --pid 26166
```

![py_spy_trace.png](images/py_spy_trace.png)

#### Version `0.4.2`
The thread panic does not cause a lockup, but the panic message is still logged:

```
thread 'statsig' panicked at /Users/runner/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/tokio-1.43.0/src/runtime/blocking/shutdown.rs:51:21:
Cannot drop a runtime in a context where blocking is not allowed. This happens when a runtime is dropped from within an asynchronous context.
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```
