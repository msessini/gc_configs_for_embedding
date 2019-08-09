import os
import stat
""" 
Script to automatically generate the configuration needed for 2016 legacy embedding. 
This script generates the AOD->MiniAOD step, 
which has to be run after the embedding procedure in CMSSW_8_0_33 
"""

final_states = ["MuTau", "ElTau", "ElMu", "TauTau", "MuEmb", "ElEmb"]
runs = [
    "Run2016B-v2", "Run2016C-v2", "Run2016D-v2", "Run2016E-v2", "Run2016F-v1",
    "Run2016G-v1", "Run2016H-v1"
]
identifier = "data_legacy_2016_CMSSW9414"
inputfolder = "Run2016_CMSSW_9_4_14_MiniAOD"


def write_while(name):
    if os.path.isfile(name + '/while.sh'):
        return
    out_file = open(name + '/while.sh', 'w')
    out_file.write('#!/bin/bash\n')
    out_file.write('\n')
    out_file.write('touch .lock\n')
    out_file.write('\n')
    out_file.write('while [ -f ".lock" ]\n')
    out_file.write('do\n')
    for akt_cfg in runs:
        out_file.write('go.py ' + akt_cfg + '.conf -G \n')
    out_file.write('echo "rm .lock"\n')
    out_file.write('sleep 2\n')
    out_file.write('done\n')
    out_file.close()
    os.chmod(name + '/while.sh', stat.S_IRWXU)


def copy_file(out_file, folder, filestream, replace_dict={}):
    if os.path.isdir(folder):
        for replace in replace_dict:  ## replace Variable by the value.
            filestream = filestream.replace(replace, replace_dict[replace])
        out_file = open("{}/{}".format(folder, out_file), 'w')
        out_file.write(filestream)
        out_file.close()


for final_state in final_states:
    # first copy the cmssw config file to the fitting folder
    script = "merging_miniaod.py"
    in_file = open("{}/{}".format(inputfolder, script), 'r')
    file_str = in_file.read()
    in_file.close()
    copy_file(script, "{}_{}".format(final_state, identifier), in_file)

    # next generate the grid-control configs
    rp_base_cfg = {}
    rp_base_cfg['__CMSRUN_ORDER__'] = script
    se_path_str = 'se path = srm://cmssrm-kit.gridka.de:8443/srm/managerv2?SFN=/pnfs/gridka.de/cms/disk-only/store/user/' + os.environ[
        "USER"] + '/gc_storage/embedding_16_legacy_miniaod'
    rp_base_cfg['__SE_PATH__'] = se_path_str
    se_output_pattern_str = 'se output pattern = ' + final_state + '_' + identifier + '/@NICK@/@FOLDER@/@XBASE@_@GC_JOB_ID@.@XEXT@'
    rp_base_cfg['__SE_OUTPUT_PATTERN__'] = se_output_pattern_str

    # finally generate the different configs for the different runs
    if final_state == "MuEmb":
        particle = "MuEmbedding"
    elif final_state == "ElEmb":
        particle = "ElEmbedding"
    else:
        particle = "TauEmbedding"
    for run in runs:
        if "naf" in os.environ["HOSTNAME"]:
            out_file = 'include=grid_control_fullembedding_data_base_naf.conf\n'
        else:
            out_file = 'include=grid_control_fullembedding_data_base_freiburg.conf\n'
        if "etp.kit.edu" in os.environ["HOSTNAME"]:
            out_file += 'workdir = /portal/{host}/home/{user}/embedding/gc_workdir/miniaod_step/{particle}_{name}\n'.format(
                host=os.environ["HOSTNAME"].replace(".ekp.kit.edu", ""),
                user=os.environ["USER"],
                particle=particle,
                name=final_state + "_" + identifier)
        elif "naf" in os.environ["HOSTNAME"]:
            out_file += 'workdir = /nfs/dust/cms/user/{user}/embedding/gc_workdir/miniaod_step/{particle}_{name}\n'.format(
                user=os.environ["USER"],
                particle=particle,
                name=final_state + "_" + identifier)
        else:
            print "Host for job submission unknown. Please set workdir manually"
        out_file += '[CMSSW]\n'
        out_file += 'dataset = {particle}_{name}_{run} :  list:{run}_aod.dbs\n'.format(
            particle=particle, name=final_state + "_" + identifier, run=run)

        copy_file("{}.conf".format(run),
                  "{}_{}".format(final_state, identifier), out_file)
    write_while(final_state + "_" + identifier)