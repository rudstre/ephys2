#### Ephys2 utility commands ####

# Main ephys2 entry point
function e2() {
    # Switch based on first argument
    case "$1" in
        "help")
            echo "Usage: e2 <command> <args>"
            echo "Commands:"
            echo "  help"
            echo "  launch <config> <job_name> {additional_sbatch_parameters}"
            echo "  launch_debug <config> <job_name> {additional_sbatch_parameters}"
            echo "  monitor <job_name>"
            echo "  stdout <job_name>"
            echo "  stderr <job_name>"
            echo "  cancel <job_name>"
            echo "  install"
            echo "  uninstall"
            echo "  gui {additional_sbatch_parameters}"
            echo "  shell"
            echo "  py {additional_sbatch_parameters}"
            echo "  squeue"
            echo "  sacct"
            ;;
        "launch")
            # Default parameters: 32 workers, 32 x 3.5GB mem, 8 hour time limit (suitable for most partitions)
            DEF_PARAMS="--partition olveczky,shared,test --ntasks-per-node 32 --mem 112000 --time 0-08:00"
            # Override defaults with passed parameters
            ACT_PARAMS="${DEF_PARAMS} ${@:4}"
            CMD="CFG=${2} sbatch -J e2_${3} -o ${EPHYS2_JOBS}/${3}.out -e ${EPHYS2_JOBS}/${3}.err ${ACT_PARAMS} ${EPHYS2_PATH}/slurm/launch.sh"
            echo "Submitting job $3."
            echo "Command: ${CMD}"
            eval $CMD
            ;;
        "launch_debug")
            # Default parameters: 32 workers, 32 x 3.5GB mem, 8 hour time limit (suitable for most partitions)
            DEF_PARAMS="--partition olveczky,shared,test --ntasks-per-node 32 --mem 112000 --time 0-08:00"
            # Override defaults with passed parameters
            ACT_PARAMS="${DEF_PARAMS} ${@:4}"
            CMD="CFG=${2} sbatch -J e2_${3} -o ${EPHYS2_JOBS}/${3}.out -e ${EPHYS2_JOBS}/${3}.err ${ACT_PARAMS} ${EPHYS2_PATH}/slurm/debug.sh"
            echo "Submitting job $3."
            echo "Command: ${CMD}"
            eval $CMD
            ;;
        "monitor")
            tail -f $EPHYS2_JOBS/$2.out $EPHYS2_JOBS/$2.err -n 1000
            ;;
        "stdout")
	        tail -f $EPHYS2_JOBS/$2.out -n 1000
            ;;
        "stderr")
        	tail -f $EPHYS2_JOBS/$2.err -n 1000
            ;;
        "cancel")
            JOB_ID=$(squeue --format="%.18i %.1000j" -u $USER | grep e2_{$2} | awk '{print $1}')
            if [[ -z "$JOB_ID" ]]; then
                echo "No job found with name $2."
            else
                echo "Cancelling job $JOB_ID."
                scancel $JOB_ID
            fi
            ;;
        "install")
	        echo "Submitting install job."
	        sbatch -J e2_install -o $EPHYS2_JOBS/install.out -e $EPHYS2_JOBS/install.err $EPHYS2_PATH/slurm/install.sh
            ;;
        "uninstall")
            echo "Submitting uninstall job."
            sbatch -J e2_uninstall -o $EPHYS2_JOBS/uninstall.out -e $EPHYS2_JOBS/uninstall.err $EPHYS2_PATH/slurm/uninstall.sh
            ;;
        "gui")
            # Check for X11 forwarding
            if ! xset q &>/dev/null
            then
                echo "No X server found. Use ssh -CY USER@login.rc.fas.harvard.edu to enable display forwarding, and make sure you are not running this from within an interactive job."
            else
                # Default parameters using remoteviz partition
                DEF_PARAMS="--partition remoteviz --ntasks-per-node 1 --nodes 1 --cpus-per-task 2 --mem 16000 --time 0-08:00"
                # Override defaults with passed parameters
                ACT_PARAMS="${DEF_PARAMS} ${@:2}"
                CMD="srun --x11=first --pty ${ACT_PARAMS} ${EPHYS2_PATH}/slurm/gui.sh"
                echo "Running command: ${CMD}"
                eval $CMD
            fi
            ;;
        "shell")
            source $EPHYS2_PATH/slurm/modules.sh
            conda activate ephys2
            ;;
        "py")
            DEF_PARAMS="--partition olveczky,shared,test --ntasks-per-node 1 --nodes 1 --cpus-per-task 4 --mem 16000 --time 0-08:00"
            # Override defaults with passed parameters
            ACT_PARAMS="${DEF_PARAMS} ${@:2}"
            CMD="srun --pty --mpi=pmix ${ACT_PARAMS} ${EPHYS2_PATH}/slurm/py.sh"
            echo "Running command: ${CMD}"
            eval $CMD
            ;;
        "squeue")
            # Filter squeue by jobs starting with e2_
            squeue -u $USER | grep e2_
            ;;
        "sacct")
            # Filter sacct by jobs starting with e2_
            sacct -u $USER | grep e2_
            ;;
        *)
            echo "Invalid command: $1"
            ;;
    esac
}
