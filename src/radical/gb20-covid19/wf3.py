import os, glob
import argparse, sys
from radical.entk import Pipeline, Stage, Task

class EsmacsTies(object):

    def __init__(self, appman, cfg):
        #self.set_argparse()
        #self._set_rmq()
        self.base_dir = cfg['work_dir']+'/'+cfg['proj']
        self.run_dir = cfg['run_dir']
        self.conda_init = cfg['conda_init']
        self.esmacs_tenv = cfg['self.conda_esmacs_task_env']
        self.esmacs_tmodules = cfg['esmacs_task_modules']
        self.am = appman
        self.pipelines = []
        self.p1 = Pipeline()
        self.p2 = Pipeline()
        self.s1 = Stage()
        self.s2 = Stage()
        self.s3 = Stage()
        self.s4 = Stage()
        self.s5 = Stage()
        self.s6 = Stage()
        self.s7 = Stage()

    # def _set_rmq(self):
    #     self.rmq_port = int(os.environ.get('RMQ_PORT', 5672))
    #     self.rmq_hostname = os.environ.get('RMQ_HOSTNAME', '129.114.17.185')
    #     self.rmq_username = os.environ.get('RMQ_USERNAME', 'litan')
    #     self.rmq_password = os.environ.get('RMQ_PASSWORD', 'sccDg7PxE3UjhA5L')

    # def set_resource(self, res_desc):
    #     res_desc["schema"] = "local"
    #     self.am.resource_desc = res_desc

    # def set_argparse(self):
    #     parser = argparse.ArgumentParser(description="ESMACS and TIES")
    #     parser.add_argument("--task", "-t", help="wf3 (ESMACS), wf4_com (TIES_com), wf4_lig (TIES_lig), hybridwf_com (ESMACS + TIES_com), or hybridwf_lig (ESMACS + TIES_lig)")
    #     parser.add_argument("--nnodes", "-n", help="Number of nodes required")
    #     args = parser.parse_args()
    #     self.args = args
    #     if args.task is None or args.nnodes is None:
    #         parser.print_help()
    #         sys.exit(-1)

    def esmacs(self, rct_stage="s1", stage="eq1", outdir="equilibration",
               name=None):

        for i in range(1, 13):
            t = Task()
            t.pre_exec = [
                "export WDIR=\"{}/{}\"".format(self.run_dir, name),
                ". {}".format(self.conda_init),
                "conda activate {}".format(self.esmacs_tenv),
                "module load {}".format(self.esmacs_tmodules),
                "mkdir -p $WDIR/replicas/rep{}/{}".format(i, outdir),
                "cd $WDIR/replicas/rep{}/{}".format(i, outdir),
                "rm -f {}.log {}.xml {}.dcd {}.chk".format(stage, stage, stage, stage),
                "export OMP_NUM_THREADS=1"
                ]
            # t.executable = '/ccs/home/litan/miniconda3/envs/wf3/bin/python3.7'
            t.executable = 'python3'
            t.arguments = ['$WDIR/{}.py'.format(stage)]
            t.post_exec = []
            t.cpu_reqs = {
                'processes': 1,
                'process_type': None,
                'threads_per_process': 4,
                'thread_type': 'OpenMP'}
            t.gpu_reqs = {
                'processes': 1,
                'process_type': None,
                'threads_per_process': 1,
                'thread_type': 'CUDA'}
            getattr(self,rct_stage).add_tasks(t)

    def ties(self, calc, ncores, rct_stage="s4", stage="eq0",
             outdir="equilibration", name=None):

        for l in [0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00]:
            for i in range(1, 6):
                t = Task()
                t.pre_exec = [
                    "module load spectrum-mpi/10.3.1.2-20200121 fftw/3.3.8",
                    "cd $MEMBERWORK/med110/test_hybridwf/{}/{}/replica-confs".format(name, calc),
                    "mkdir -p ../LAMBDA_{:.2f}/rep{}/{}".format(l, i, outdir),
                    "export OMP_NUM_THREADS=1"
                    ]
                t.executable = '/gpfs/alpine/world-shared/bip115/NAMD_binaries/summit/NAMD_LATEST_Linux-POWER-MPI-smp-Summit/namd2'
                t.arguments = ['+ppn', '41', '--tclmain', '{}.conf'.format(stage), '{:.2f}'.format(l), '{}'.format(i)]#'{}'.format(ncores)
                t.post_exec = []
                t.cpu_reqs = {
                    'processes': 1,
                    'process_type': None,#'MPI'
                    'threads_per_process': 4*int(ncores),#amounts to 35 cores per node (out of 41 usable cores)
                    'thread_type': 'OpenMP'
                }
                getattr(self,rct_stage).add_tasks(t)

    def run(self):
        self.am.workflow = self.pipelines#[self.p]
        self.am.run()

    def wf3(self):
        '''self.p1 = Pipeline()
        pipelines.append(self.p1)
        self.s1 = Stage()
        self.s2 = Stage()
        self.s3 = Stage()'''

        esmacs_names = glob.glob("{}/input/lig*".format(self.run_dir))
        for comp in esmacs_names:
            self.esmacs(name=comp)
        self.p1.add_stages(self.s1)

        for comp in esmacs_names:
            self.esmacs(rct_stage="s2", stage="eq2", name=comp)
        self.p1.add_stages(self.s2)

        for comp in esmacs_names:
            self.esmacs(rct_stage="s3", stage="sim1", outdir="simulation", name=comp)
        self.p1.add_stages(self.s3)

        self.pipelines.append(self.p1)

    # def wf4(self, calc="com", ncores="35"):
    #     '''self.p2 = Pipeline()
    #     pipelines.append(self.p2)
    #     self.s4 = Stage()
    #     self.s5 = Stage()
    #     self.s6 = Stage()
    #     self.s7 = Stage()'''

    #     ties_names = glob.glob("input/ties-*")

    #     for comp in ties_names:
    #         self.ties(calc, ncores, name=comp)
    #     self.p2.add_stages(self.s4)

    #     for comp in ties_names:
    #         self.ties(calc, ncores, rct_stage="s5", stage="eq1", name=comp)
    #     self.p2.add_stages(self.s5)

    #     for comp in ties_names:
    #         self.ties(calc, ncores, rct_stage="s6", stage="eq2", name=comp)
    #     self.p2.add_stages(self.s6)

    #     for comp in ties_names:
    #         self.ties(calc, ncores, rct_stage="s7", stage="sim1", outdir="simulation", name=comp)
    #     self.p2.add_stages(self.s7)

    #     self.pipelines.append(self.p2)


# if __name__ == "__main__":

#     esmacs_ties = EsmacsTies()

#     n_nodes = int(esmacs_ties.args.nnodes)
#     esmacs_ties.set_resource(res_desc = {
#         'resource': 'ornl.summit',
#         'queue'   : 'debug',
#         'walltime': 120, #MIN
#         'cpus'    : 168 * n_nodes,
#         'gpus'    : 6 * n_nodes,
#         'project' : 'MED110'
#         })

#     #pipelines = []

#     if esmacs_ties.args.task == "wf3":
#         esmacs_ties.wf3()
#         esmacs_ties.run()

#     elif esmacs_ties.args.task == "wf4_com":
#         esmacs_ties.wf4(ncores="41")
#         esmacs_ties.run()

#     elif esmacs_ties.args.task == "wf4_lig":
#         esmacs_ties.wf4(calc="lig", ncores="8")
#         esmacs_ties.run()

#     elif esmacs_ties.args.task == "hybridwf_com":
#         esmacs_ties.wf3()
#         esmacs_ties.wf4()
#         esmacs_ties.run()

#     elif esmacs_ties.args.task == "hybridwf_lig":
#         esmacs_ties.wf3()
#         esmacs_ties.wf4(calc="lig", ncores="7")
#         esmacs_ties.run()
